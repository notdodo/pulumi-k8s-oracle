from pulumi import Config  # pyright: reportShadowedImports=false
from resources.compartment import Compartment
from resources.network import Network
from resources.instance import Instance
from resources.outputs import outputs
import pulumi_oci as oci

config = Config()

compartment = Compartment().create_compartment(config)
vcn = Network().create_vcn(config, compartment)
subnet = Network().create_subnet(config, compartment, vcn)
internet_gateway = Network().create_internet_gateway(config, compartment, vcn)
route_table_internet = Network().create_route_table(
    config,
    compartment,
    vcn,
    subnet,
    internet_gateway,
)
instance = Instance().create_instaces(config, compartment, subnet)

outputs(instance)
