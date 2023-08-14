import json  # pyright: ignore[reportShadowedImports]
import os
import stat

import pulumi
import pulumi_command as pc
import pulumi_tls

import resources.dns as dns
from resources.compartment import Compartment
from resources.instance import Instance
from resources.network import Network
from resources.outputs import outputs

config = pulumi.Config()
private_key = ""
public_key = ""

if pulumi.get_stack() == "master":
    node_config = json.loads(config.get("masters_config"))[0]
else:
    node_config = json.loads(config.get("workers_config"))[0]

if not (os.path.exists("ssh_priv.key") and os.path.exists("ssh_pub.key")):
    private_key_resource = pulumi_tls.PrivateKey(
        "k8sPrivateKey",
        algorithm="ED25519",
    )
    public_key = private_key_resource.public_key_openssh
    private_key = private_key_resource.private_key_openssh

    def write_to_file(what, file):
        with open(file, "w") as f:
            f.write(what)
        os.chmod(file, stat.S_IRWXU)

    private_key.apply(lambda x: write_to_file(x, "ssh_priv.key"))
    public_key.apply(lambda x: write_to_file(x, "ssh_pub.key"))
else:
    private_key = open("ssh_priv.key").read()
    public_key = open("ssh_pub.key").read()

node_config["private_key"] = private_key
node_config["public_key"] = public_key

compartment = Compartment(config.require("compartment_name"))
network = Network(
    compartment=compartment,
    node_config=config,
    instance_name=node_config.get("instance_name"),
    opts=pulumi.ResourceOptions(depends_on=compartment),
)

network.create_vcn()
network.create_subnet()
network.create_internet_gateway()
network.create_route_table()

instance_extra_cmds = []
master_ip = ""

not_this_node = (
    json.loads(config.get("workers_config"))[0]
    if pulumi.get_stack() == "master"
    else json.loads(config.get("masters_config"))[0]
)

user_data_substitutions = {
    "##PODSUBNET##": config.require("pod_subnet"),
    "##PRIVATEIP##": node_config.get("private_ip"),
    "##PUBLICDOMAIN##": f"k8s.{config.require('base_domain')}",
    "##CRIOVERSION##": config.require("crio_version"),
}

if "worker" in pulumi.get_stack():
    master_ip = json.loads(os.popen('pulumi stack output -s master -j').read()).get("instance_ip")
    user_data_substitutions["##PEERIP##"] = master_ip
    connection = pc.remote.ConnectionArgs(
        user="ubuntu",
        host=master_ip,
        private_key=open("ssh_priv.key", "r").read(),
    )
    token = pc.remote.Command(
        "kubadmToken",
        connection=connection,
        create="sudo kubeadm token create --print-join-command",
    )
    instance_extra_cmds.append(token.stdout)

instance = Instance(
    compartment=compartment,
    network=network,
    node_config=node_config,
    opts=pulumi.ResourceOptions(depends_on=compartment),
)
node = instance.create_instance(
    extra_cmds=instance_extra_cmds,
    substitutions=user_data_substitutions,
)
outputs(node)


if "master" in pulumi.get_stack():
    dns.create_dns_records(node.public_ip)