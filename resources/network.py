import pulumi_oci as oci


class Network:
    __compartment = ""
    __vcn = ""
    __internet_gateway = ""
    __subnet = ""
    __route_table = ""
    __config = ""

    def __init__(self, config, compartment) -> None:
        self.__config = config
        self.__compartment = compartment

    def create_vcn(
        self,
    ):
        if self.__vcn != "":
            print("VNC already present!")
            return
        try:
            self.__vcn = oci.core.Vcn(
                "{}VCN".format(self.__config.get("prefix")),
                cidr_blocks=[self.__config.get("vcn_cidr_block")],
                compartment_id=self.__compartment.id,
                display_name="{}VCN".format(self.__config.get("prefix")),
            )
        except Exception as err:
            print("Error creating VCN: ", str(err))

    def create_internet_gateway(self):
        if self.__internet_gateway != "":
            print("Internet Gateway already present!")
            return
        try:
            self.__internet_gateway = oci.core.InternetGateway(
                resource_name="{}InternetGateway".format(self.__config.get("prefix")),
                compartment_id=self.__compartment.id,
                vcn_id=self.__vcn.id,
            )
        except Exception as err:
            print("Error creating InternetGateway: ", str(err))

    def create_subnet(self):
        if self.__subnet != "":
            print("Subnet already present!")
            return
        try:
            self.__subnet = oci.core.Subnet(
                compartment_id=self.__compartment.id,
                resource_name="{}Subnet1".format(self.__config.get("prefix")),
                vcn_id=self.__vcn.id,
                cidr_block=self.__config.get("instance_nodesubnet_cidr"),
                display_name="{}Subnet1".format(self.__config.get("prefix")),
                security_list_ids=[
                    self.__vcn.default_security_list_id,
                ],
                prohibit_public_ip_on_vnic=False,
                route_table_id=self.__vcn.default_route_table_id,
                dhcp_options_id=self.__vcn.default_dhcp_options_id,
            )
        except Exception as err:
            print("Error creating Subnet: ", str(err))

    def create_route_table(self):
        if self.__route_table != "":
            print("DefaultRouteTable already present!")
            return
        try:
            route_table = oci.core.DefaultRouteTable(
                compartment_id=self.__compartment.id,
                resource_name="{}RouteTable".format(self.__config.get("prefix")),
                route_rules=[
                    oci.core.RouteTableRouteRuleArgs(
                        network_entity_id=self.__internet_gateway.id,
                        destination="0.0.0.0/0",
                        destination_type="CIDR_BLOCK",
                    )
                ],
                manage_default_resource_id=self.__subnet.route_table_id,
            )
            oci.core.RouteTableAttachment(
                resource_name="RouteTable",
                subnet_id=self.__.id,
                route_table_id=route_table.id,
            )
        except Exception as err:
            print("Error creating RouteTable: ", str(err))

    def get_subnet(self):
        return self.__subnet
