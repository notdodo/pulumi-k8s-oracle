from pulumi import Config  # pyright: reportShadowedImports=false

import resources.dns as dns
from resources.compartment import Compartment
from resources.instance import Instance
from resources.network import Network
from resources.outputs import outputs

config = Config()

compartment = Compartment(config.get("compartment_id"))
network = Network(config=config, compartment=compartment)

network.create_vcn()
network.create_subnet()
network.create_internet_gateway()
network.create_route_table()

instance = Instance().create_instance(compartment, network.get_subnet())
outputs(instance)
dns.create_dns_records(instance.public_ip)
