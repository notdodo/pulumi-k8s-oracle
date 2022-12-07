import pulumi_oci as oci


class Network:
    def create_vcn(self, config, compartment):
        try:
            return oci.core.Vcn(
                "{}VCN".format(config.get("prefix")),
                cidr_blocks=[config.get("vcn_cidr_block")],
                compartment_id=compartment.id,
                display_name="{}VCN".format(config.get("prefix")),
            )
        except Exception as err:
            print("Error creating VCN: ", str(err))

    def create_internet_gateway(self, config, compartment, vcn):
        try:
            return oci.core.InternetGateway(
                resource_name="{}InternetGateway".format(config.get("prefix")),
                compartment_id=compartment.id,
                vcn_id=vcn.id,
            )
        except Exception as err:
            print("Error creating InternetGateway: ", str(err))

    def create_subnet(self, config, compartment, vcn):
        try:
            return oci.core.Subnet(
                compartment_id=compartment.id,
                resource_name="{}Subnet1".format(config.get("prefix")),
                vcn_id=vcn.id,
                cidr_block=config.get("instance_nodesubnet_cidr"),
                display_name="{}Subnet1".format(config.get("prefix")),
                security_list_ids=[
                    vcn.default_security_list_id,
                ],
                prohibit_public_ip_on_vnic=False,
                route_table_id=vcn.default_route_table_id,
                dhcp_options_id=vcn.default_dhcp_options_id,
            )
        except Exception as err:
            print("Error creating Subnet: ", str(err))

    def create_route_table(self, config, compartment, vcn, subnet, internet_gateway):
        try:
            route_table = oci.core.DefaultRouteTable(
                compartment_id=compartment.id,
                resource_name="{}RouteTable".format(config.get("prefix")),
                route_rules=[
                    oci.core.RouteTableRouteRuleArgs(
                        network_entity_id=internet_gateway.id,
                        destination="0.0.0.0/0",
                        destination_type="CIDR_BLOCK",
                    )
                ],
                manage_default_resource_id=subnet.route_table_id,
            )
            oci.core.RouteTableAttachment(
                resource_name="RouteTable",
                subnet_id=subnet.id,
                route_table_id=route_table.id,
            )
            return route_table
        except Exception as err:
            print("Error creating RouteTable: ", str(err))
