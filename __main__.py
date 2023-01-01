from pulumi import Config  # pyright: reportShadowedImports=false
from resources.compartment import Compartment
from resources.network import Network
from resources.instance import Instance
from resources.outputs import outputs

config = Config()

compartment = Compartment(config.get("compartment_id"))
network = Network(config=config, compartment=compartment)

network.create_vcn()
network.create_subnet()
network.create_internet_gateway()
network.create_route_table()

instance = Instance().create_instaces(config, compartment, network.get_subnet())
outputs(instance)
