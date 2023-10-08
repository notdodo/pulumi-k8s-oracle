import base64  # pyright: ignore[reportShadowedImports]

import jinja2
import pulumi
import pulumi_command as pc
import pulumi_oci as oci

import resources.dns as cloudflare
import wireguard as wg
from resources.compartment import Compartment
from resources.instance import Instance
from resources.network import Network
from resources.ssh_keys import generate_ssh_keys

config = pulumi.Config()
instances = config.require_object("instances")
private_key, public_key = generate_ssh_keys()


def create_template(path: str) -> jinja2.Template:
    with open(path, "r") as f:
        return jinja2.Template(f.read())


bootstrap_template = create_template("./cloud-init-bootstrap_node.yaml")
master_template = create_template("./cloud-init-master.yaml")
worker_template = create_template("./cloud-init-worker.yaml")

crio_version = config.require("crio_version")
cluster_name = config.require("cluster_name")
pod_subnet = config.require("cluster_pod_subnet")
service_subnet = config.require("cluster_service_subnet")
control_plane_endpoint = f"k8s.{config.require('base_domain')}"
etc_hosts = [
    {
        "hostname": instance["name"],
        "private_ip": instance["private_ip"],
        "wg_ip": instance["wg_ip"],
    }
    for instance in instances
]

for instance in instances:
    oci_profile = instance["oci_profile"]
    provider = oci.Provider(
        f"{instance['oci_profile']}",
        config_file_profile=instance["oci_profile"],
    )

    compartment = Compartment(
        compartment_name=f"k8s_cluster_{instance['name']}",
        opts=pulumi.ResourceOptions(provider=provider),
    )
    network = Network(
        name=instance["name"],
        compartment=compartment,
        vcn_cidr_block=config.require("vcn_cidr_block"),
        subnet_cidr=instance["subnet_cidr"],
        opts=pulumi.ResourceOptions(depends_on=compartment, provider=provider),
    )

    public_ip = network.public_ip
    instance["provider"] = provider
    instance["compartment"] = compartment
    instance["public_ip"] = public_ip
    instance["public_ip_id"] = network.public_ip_id
    instance["network"] = network
    instance["wg_private"] = config.require_secret(f"{instance['name']}_wg_private_key")
    instance["wg_public"] = config.require_secret(f"{instance['name']}_wg_public_key")
    pulumi.export(f"\"{instance['name']}\" public IP:", instance["public_ip"])

for instance in instances:
    instance["wg_config"] = wg.generate_config(
        interface=instance["wg_ip"],
        private_key=instance["wg_private"],
        peers=[
            {
                "public_ip": inst["public_ip"],
                "public_key": inst["wg_public"],
                "allowed_ips": f"{inst['private_ip']}/32,{inst['wg_ip']}/32,"
                + config.require("cluster_pod_subnet")
                + ","
                + config.require("cluster_service_subnet"),
            }
            for inst in instances
            if inst["name"] is not instance["name"]
        ],
    )

    if instance.get("cluster_bootstrap", False):
        for record in config.require_object("cloudflare")[0]["records"]:
            cloudflare.create_dns_records(
                instance["name"], instance["public_ip"], record
            )
        instance["user_data"] = pulumi.Output.all(
            wg_config=instance["wg_config"], instance=instance
        ).apply(
            lambda args: base64.b64encode(
                bytes(
                    bootstrap_template.render(
                        crio_version=crio_version,
                        etc_hosts=etc_hosts,
                        cluster_advertise_address=args["instance"]["wg_ip"],
                        cluster_name=cluster_name,
                        control_plane_endpoint=control_plane_endpoint,
                        pod_subnet=pod_subnet,
                        service_subnet=service_subnet,
                        wireguard_config=args["wg_config"],
                        keepalived_password=config.get_secret("keepalived_password"),
                    ),
                    "utf-8",
                )
            ).decode("utf-8")
        )
    elif instance.get("is_controlplane", False):
        instance["user_data"] = pulumi.Output.all(
            wg_config=instance["wg_config"], instance=instance
        ).apply(
            lambda args: base64.b64encode(
                bytes(
                    master_template.render(
                        crio_version=crio_version,
                        etc_hosts=etc_hosts,
                        cluster_advertise_address=instance["wg_ip"],
                        wireguard_config=args["wg_config"],
                        keepalived_password=config.get_secret("keepalived_password"),
                    ),
                    "utf-8",
                )
            ).decode("utf-8")
        )
    else:
        instance["user_data"] = pulumi.Output.all(
            wg_config=instance["wg_config"], instance=instance
        ).apply(
            lambda args: base64.b64encode(
                bytes(
                    worker_template.render(
                        crio_version=crio_version,
                        etc_hosts=etc_hosts,
                        cluster_advertise_address=instance["wg_ip"],
                        wireguard_config=args["wg_config"],
                    ),
                    "utf-8",
                )
            ).decode("utf-8")
        )

    instance["instance"] = Instance(
        name=instance["name"],
        compartment=instance["compartment"],
        network=instance["network"],
        user_data=instance["user_data"],
        private_ip=instance["private_ip"],
        public_ip_id=instance["public_ip_id"],
        provider=instance["provider"],
        public_key=public_key,
    ).create_instance()

connection = pc.remote.ConnectionArgs(
    user="ubuntu",
    host=[
        instance["public_ip"]
        for instance in instances
        if instance.get("cluster_bootstrap", False) and "instance" in instance
    ][0],
    private_key=open("ssh_priv.key", "r").read(),
)

controlplane_join_cmd = (
    "while ! grep -q 'successfully' /var/log/cloud-init-output.log; do sleep 1; done;"
    + "echo sudo $(sudo kubeadm token create --print-join-command) "
    + "--control-plane --certificate-key $(sudo kubeadm init phase "
    + "upload-certs --upload-certs | grep -vw -e certificate -e Namespace);"
    + 'echo "sleep 1; sudo shutdown -r now" | at now'
)

join_cmd = pulumi.Output.concat(
    "while ! command -v kubeadm; do sleep 1; done; sleep 10;",
    pc.remote.Command(
        "join_command",
        connection=connection,
        create=controlplane_join_cmd,
        update=controlplane_join_cmd,
        triggers=[i["instance"].id for i in instances],
    ).stdout,
)

for instance in instances:
    if instance.get("is_controlplane", False) and not instance.get(
        "cluster_bootstrap", False
    ):
        connection = pc.remote.ConnectionArgs(
            user="ubuntu",
            host=instance["public_ip"],
            private_key=open("ssh_priv.key", "r").read(),
        )

        join_cmd = pulumi.Output.concat(
            join_cmd,
            f" --apiserver-advertise-address {instance['wg_ip']}; sleep 20;",
            "sudo KUBECONFIG=/etc/kubernetes/admin.conf ",
            f"kubectl taint nodes {instance['name']} ",
            "node-role.kubernetes.io/control-plane:NoSchedule-",
        )
        cp_join = pc.remote.Command(
            f"join_{instance['name']}",
            connection=connection,
            create=join_cmd,
            update=pulumi.Output.concat("sudo kubeadm reset --force;", join_cmd),
            triggers=[i["instance"].id for i in instances],
        )

        for record in config.require_object("cloudflare")[0]["records"]:
            cloudflare.create_dns_records(
                instance["name"],
                instance["public_ip"],
                record,
                deps=[cp_join],
            )
