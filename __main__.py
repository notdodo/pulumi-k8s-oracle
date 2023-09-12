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
worker_template = create_template("./cloud-init-worker.yaml")
master_template = create_template("./cloud-init-master.yaml")

crio_version = config.require("crio_version")
cluster_name = config.require("cluster_name")
pod_subnet = config.require("cluster_pod_subnet")
service_subnet = config.require("cluster_service_subnet")
control_plane_endpoint = f"k8s.{config.require('base_domain')}"
etc_hosts = [
    {
        "hostname": instance["name"],
        "private_ip": instance.get("private_ip"),
        "wg_ip": instance.get("wg_ip"),
    }
    for instance in instances
]

for i, instance in enumerate(instances):
    oci_profile = instance.get("oci_profile")
    provider = oci.Provider(
        f"{instance.get('oci_profile')}",
        config_file_profile=instance.get("oci_profile"),
    )

    compartment = Compartment(
        compartment_name=f"k8s_cluster_{instance.get('name')}",
        opts=pulumi.ResourceOptions(provider=provider),
    )
    network = Network(
        name=instance.get("name"),
        compartment=compartment,
        vcn_cidr_block=config.require("vcn_cidr_block"),
        subnet_cidr=instance.get("subnet_cidr"),
        opts=pulumi.ResourceOptions(depends_on=compartment, provider=provider),
    )

    public_ip = network.public_ip
    instances[i]["provider"] = provider
    instances[i]["compartment"] = compartment
    instances[i]["public_ip"] = public_ip
    instances[i]["public_ip_id"] = network.public_ip_id
    instances[i]["network"] = network
    instances[i]["wg_private"] = config.require_secret(
        f"{instance.get('name')}_wg_private_key"
    )
    instances[i]["wg_public"] = config.require_secret(
        f"{instance.get('name')}_wg_public_key"
    )
    pulumi.export(f"\"{instance.get('name')}\" public IP:", public_ip)

for i, instance in enumerate(instances):
    wg_config = wg.generate_config(
        interface=instance["wg_ip"],
        private_key=instance["wg_private"],
        peers=[
            {
                "public_ip": inst.get("public_ip"),
                "public_key": inst.get("wg_public"),
                "allowed_ips": f"{inst.get('private_ip')}/32,{inst.get('wg_ip')}/32,"
                + config.require("cluster_pod_subnet")
                + ","
                + config.require("cluster_service_subnet"),
            }
            for inst in instances
            if inst.get("name") is not instance.get("name")
        ],
    )

    if instance.get("cluster_bootstrap"):
        user_data = pulumi.Output.all(
            wg_config=wg_config,
        ).apply(
            lambda wg_config: base64.b64encode(
                bytes(
                    bootstrap_template.render(
                        crio_version=crio_version,
                        etc_hosts=etc_hosts,
                        cluster_advertise_address=instance["wg_ip"],
                        cluster_name=cluster_name,
                        control_plane_endpoint=control_plane_endpoint,
                        pod_subnet=pod_subnet,
                        service_subnet=service_subnet,
                        wireguard_config=wg_config["wg_config"],
                    ),
                    "utf-8",
                )
            ).decode("utf-8")
        )
    elif instance.get("is_controlplane"):
        user_data = pulumi.Output.all(
            wg_config=wg_config,
        ).apply(
            lambda wg_config: base64.b64encode(
                bytes(
                    master_template.render(
                        crio_version=crio_version,
                        etc_hosts=etc_hosts,
                        cluster_advertise_address=instance.get("wg_ip"),
                        cluster_name=cluster_name,
                        control_plane_endpoint=control_plane_endpoint,
                        pod_subnet=pod_subnet,
                        service_subnet=service_subnet,
                        wireguard_config=wg_config["wg_config"],
                        bootstrap_node_hostname=instance.get("name"),
                    ),
                    "utf-8",
                )
            ).decode("utf-8")
        )
    else:
        user_data = pulumi.Output.all(
            wg_config=wg_config,
        ).apply(
            lambda wg_config: base64.b64encode(
                bytes(
                    worker_template.render(
                        crio_version=crio_version,
                        etc_hosts=etc_hosts,
                        cluster_advertise_address=instance["wg_ip"],
                        cluster_name=cluster_name,
                        control_plane_endpoint=control_plane_endpoint,
                        pod_subnet=pod_subnet,
                        service_subnet=service_subnet,
                        wireguard_config=wg_config["wg_config"],
                        bootstrap_node_hostname=instance["name"],
                    ),
                    "utf-8",
                )
            ).decode("utf-8")
        )

    instances[i]["user_data"] = user_data


for i, instance in enumerate(instances):
    instances[i]["instance"] = Instance(
        name=instance["name"],
        compartment=instance["compartment"],
        network=instance["network"],
        user_data=instance["user_data"],
        private_ip=instance["private_ip"],
        public_ip_id=instance["public_ip_id"],
        provider=instance["provider"],
        public_key=public_key,
    ).create_instance()

for instance in instances:
    if instance.get("is_controlplane"):
        for record in config.require_object("cloudflare")[0].get("records"):
            cloudflare.create_dns_records(
                instance.get("name"), instance["public_ip"], record
            )

connection = pc.remote.ConnectionArgs(
    user="ubuntu",
    host=[
        instance.get("public_ip")
        for instance in instances
        if instance.get("cluster_bootstrap")
    ][0],
    private_key=open("ssh_priv.key", "r").read(),
)

controlplane_join_cmd = (
    "while ! grep -q 'successfully' /var/log/cloud-init-output.log; do sleep 1; done;"
    + "echo sudo $(sudo kubeadm token create --print-join-command) "
    + "--control-plane --certificate-key $(sudo kubeadm init phase "
    + "upload-certs --upload-certs | grep -vw -e certificate -e Namespace)"
)

join_cmd = pulumi.Output.concat(
    "while ! command -v kubeadm; do sleep 1; done;",
    pc.remote.Command(
        "join_command",
        connection=connection,
        create=controlplane_join_cmd,
        update=controlplane_join_cmd,
        triggers=[i["instance"].id for i in instances],
    ).stdout,
)

for instance in instances:
    if instance.get("is_controlplane") and not instance.get("cluster_bootstrap"):
        connection = pc.remote.ConnectionArgs(
            user="ubuntu",
            host=instance.get("public_ip"),
            private_key=open("ssh_priv.key", "r").read(),
        )

        join_cmd = pulumi.Output.concat(
            join_cmd,
            " --apiserver-advertise-address ",
            instance.get("wg_ip"),
        )
        pc.remote.Command(
            f"join_{instance.get('name')}",
            connection=connection,
            create=join_cmd,
            update=join_cmd,
            triggers=[i["instance"].id for i in instances],
        )
