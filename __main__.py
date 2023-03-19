from pulumi import Config, ResourceOptions  # pyright: reportShadowedImports=false

import resources.dns as dns
from resources.compartment import Compartment
from resources.instance import Instance
from resources.network import Network
from resources.outputs import outputs

config = Config()

compartment = Compartment("k8smaster")
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
dns.create_dns_records(node.public_ip)
