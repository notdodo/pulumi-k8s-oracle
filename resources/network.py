from typing import Optional

import pulumi
import pulumi_oci as oci

from resources.compartment import Compartment


class Network(pulumi.ComponentResource):
    __compartment = ""
    __vcn = ""
    __internet_gateway = ""
    __subnet = ""
    __route_table = ""
    __config = ""

    def __init__(
        self,
        compartment: Compartment,
        node_config: dict,
        instance_name: str,
        props: Optional[pulumi.Inputs] = None,
        opts: Optional[pulumi.ResourceOptions] = None,
        remote: bool = False,
    ) -> None:
        super().__init__("oracle:network", "oracle:network", props, opts, remote)
        self.__child_opts = pulumi.ResourceOptions(
            parent=self,
            delete_before_replace=True,
        )
        self.__compartment = compartment
        self.__config = node_config
        self.instance_name = instance_name

    def create_vcn(self):
        self.__vcn = oci.core.Vcn(
            "{}VCN".format(self.instance_name),
            cidr_blocks=[self.__config.get("vcn_cidr_block")],
            compartment_id=self.__compartment.id,
            display_name="{}VCN".format(self.instance_name),
            byoipv6cidr_details=[],
            opts=self.__child_opts,
        )

    def create_internet_gateway(self):
        self.__internet_gateway = oci.core.InternetGateway(
            resource_name="{}InternetGateway".format(self.instance_name),
            compartment_id=self.__compartment.id,
            vcn_id=self.__vcn.id,
            opts=self.__child_opts,
        )

    def create_subnet(self):
        custom_security_list = oci.core.SecurityList(
            compartment_id=self.__compartment.id,
            resource_name="k8sSecList",
            vcn_id=self.__vcn.id,
            display_name="k8sSecList",
            egress_security_rules=[
                oci.core.SecurityListEgressSecurityRuleArgs(
                    protocol="all",
                    destination="0.0.0.0/0",
                    description="Allow all outbound traffic",
                )
            ],
            ingress_security_rules=[
                oci.core.SecurityListIngressSecurityRuleArgs(
                    protocol="17",  # udp
                    source="0.0.0.0/0",
                    udp_options=oci.core.SecurityListIngressSecurityRuleUdpOptionsArgs(
                        max=51000,
                        min=51000,
                    ),
                    description="Allow in UDP for Wireguard",
                ),
                oci.core.SecurityListIngressSecurityRuleArgs(
                    protocol="6",  # tcp
                    source="0.0.0.0/0",
                    tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                        max=22,
                        min=22,
                    ),
                    description="Allow in TCP for SSH",
                ),
                oci.core.SecurityListIngressSecurityRuleArgs(
                    protocol="6",  # tcp
                    source="0.0.0.0/0",
                    tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                        max=443,
                        min=443,
                    ),
                    description="Allow in TCP for HTTPS",
                ),
                oci.core.SecurityListIngressSecurityRuleArgs(
                    protocol="6",  # tcp
                    source="0.0.0.0/0",
                    tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                        max=80,
                        min=80,
                    ),
                    description="Allow in TCP for HTTP",
                ),
            ],
            opts=self.__child_opts,
        )

        self.__subnet = oci.core.Subnet(
            compartment_id=self.__compartment.id,
            resource_name="{}Subnet".format(self.instance_name),
            vcn_id=self.__vcn.id,
            cidr_block=self.__config.get("instance_subnet_cidr"),
            display_name="{}Subnet".format(self.instance_name),
            security_list_ids=[
                custom_security_list,
            ],
            prohibit_public_ip_on_vnic=False,
            route_table_id=self.__vcn.default_route_table_id,
            dhcp_options_id=self.__vcn.default_dhcp_options_id,
            opts=self.__child_opts,
        )

    def create_route_table(self):
        self.__route_table = oci.core.DefaultRouteTable(
            compartment_id=self.__compartment.id,
            resource_name="{}RouteTable".format(self.instance_name),
            route_rules=[
                oci.core.RouteTableRouteRuleArgs(
                    network_entity_id=self.__internet_gateway.id,
                    destination="0.0.0.0/0",
                    destination_type="CIDR_BLOCK",
                )
            ],
            manage_default_resource_id=self.__subnet.route_table_id,
            opts=self.__child_opts,
        )
        oci.core.RouteTableAttachment(
            resource_name="RouteTable",
            subnet_id=self.__subnet.id,
            route_table_id=self.__route_table.id,
            opts=self.__child_opts,
        )

    def get_subnet(self):
        return self.__subnet
