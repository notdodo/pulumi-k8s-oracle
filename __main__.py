import pulumi_command as pc
from pulumi import Config  # pyright: reportShadowedImports=false
from pulumi import ResourceOptions, get_stack

import resources.dns as dns
from resources.compartment import Compartment
from resources.instance import Instance
from resources.network import Network
from resources.outputs import outputs

config = Config()

compartment = Compartment(config.get("compartment_name"))
network = Network(
    compartment=compartment,
    opts=ResourceOptions(depends_on=compartment),
)

network.create_vcn()
network.create_subnet()
network.create_internet_gateway()
network.create_route_table()

instance = Instance(
    compartment=compartment,
    network=network,
    opts=ResourceOptions(depends_on=compartment),
)
node = instance.create_instance()
outputs(node)


if "k8s-master" in get_stack():
    dns.create_dns_records(node.public_ip)
else:
    token = pc.remote.Command(
        "kubadmToken",
        connection=pc.remote.ConnectionArgs(
            host="k8s.thedodo.xyz",
            port=22,
            private_key=open(
                config.get("path_ssh_privkey"),
                "r",
            ).read(),
        ),
        create="kubeadm token create --print-join-command",
        opts=ResourceOptions(depends_on=node),
    )
