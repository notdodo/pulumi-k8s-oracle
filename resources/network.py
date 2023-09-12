from typing import Optional

import pulumi
import pulumi_oci as oci
from requests import get

from resources.compartment import Compartment


class Network(pulumi.ComponentResource):
    _compartment = ""
    _vcn = ""
    _internet_gateway = ""
    _subnet = ""
    _route_table = ""
    _config = ""

    def __init__(
        self,
        name: str,
        compartment: Compartment,
        vcn_cidr_block: str,
        subnet_cidr: str,
        props: Optional[pulumi.Inputs] = None,
        opts: Optional[pulumi.ResourceOptions] = None,
        remote: bool = False,
    ) -> None:
        super().__init__("oracle:network", f"network_{name}", props, opts, remote)
        self._child_opts = pulumi.ResourceOptions(
            parent=self,
            delete_before_replace=True,
        )
        self._compartment = compartment
        self._instance_name = name
        self._vcn_cidr_block = vcn_cidr_block
        self._subnet_cidr = subnet_cidr
        self.create_network()

    def my_public_ip(self):
        return get("https://ifconfig.me").content.decode("utf8")

    @property
    def vcn(self) -> oci.core.Vcn:
        return self._vcn

    @property
    def subnet(self) -> oci.core.Subnet:
        return self._subnet

    @property
    def internet_gateway(self) -> oci.core.InternetGateway:
        return self._internet_gateway

    @property
    def public_ip(self) -> str:
        return self._public_ip.ip_address

    @property
    def public_ip_id(self) -> str:
        return self._public_ip.id

    def create_network(self):
        self._create_vcn()
        self._create_security_list()
        self._create_subnet()
        self._create_internet_gateway()
        self._create_route_table()
        self._create_public_ip()

    def _create_public_ip(self):
        self._public_ip = oci.core.PublicIp(
            f"public_ip_{self._instance_name}",
            compartment_id=self._compartment.id,
            lifetime="RESERVED",
            opts=self._child_opts,
        )

    def _create_vcn(self):
        self._vcn = oci.core.Vcn(
            f"vcn_{self._instance_name}",
            cidr_blocks=[self._vcn_cidr_block],
            compartment_id=self._compartment.id,
            display_name=f"vcn_{self._instance_name}",
            byoipv6cidr_details=[],
            opts=self._child_opts,
        )

    def _create_internet_gateway(self):
        self._internet_gateway = oci.core.InternetGateway(
            resource_name=f"igw_{self._instance_name}",
            compartment_id=self._compartment.id,
            vcn_id=self._vcn.id,
            opts=self._child_opts,
        )

    def _create_security_list(self):
        self._custom_security_list = oci.core.SecurityList(
            compartment_id=self._compartment.id,
            resource_name=f"seclist_{self._instance_name}",
            vcn_id=self._vcn.id,
            display_name=f"seclist_{self._instance_name}",
            egress_security_rules=[
                oci.core.SecurityListEgressSecurityRuleArgs(
                    protocol="all",
                    destination="0.0.0.0/0",
                    description="Allow all outbound traffic",
                )
            ],
            ingress_security_rules=[
                oci.core.SecurityListIngressSecurityRuleArgs(
                    protocol="6",
                    source="0.0.0.0/0",
                    description="SSH",
                    tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                        max="22",
                        min="22",
                    ),
                ),
                oci.core.SecurityListIngressSecurityRuleArgs(
                    protocol="17",
                    source="0.0.0.0/0",
                    description="Wireguard VPN",
                    udp_options=oci.core.SecurityListIngressSecurityRuleUdpOptionsArgs(
                        max="51000",
                        min="51000",
                    ),
                ),
                oci.core.SecurityListIngressSecurityRuleArgs(
                    protocol="6",
                    source="0.0.0.0/0",
                    description="Control Plane",
                    tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                        max="2016",
                        min="2016",
                    ),
                ),
                oci.core.SecurityListIngressSecurityRuleArgs(
                    protocol="6",
                    source="0.0.0.0/0",
                    description="HTTPS",
                    tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                        max="443",
                        min="443",
                    ),
                ),
                oci.core.SecurityListIngressSecurityRuleArgs(
                    protocol="6",
                    source="0.0.0.0/0",
                    description="HTTP",
                    tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                        max="80",
                        min="80",
                    ),
                ),
            ],
            opts=self._child_opts,
        )

    def _create_subnet(self):
        self._subnet = oci.core.Subnet(
            compartment_id=self._compartment.id,
            resource_name=f"subnet_{self._instance_name}",
            vcn_id=self._vcn.id,
            cidr_block=self._subnet_cidr,
            display_name=f"subnet_{self._instance_name}",
            security_list_ids=[
                self._custom_security_list,
            ],
            prohibit_public_ip_on_vnic=False,
            route_table_id=self._vcn.default_route_table_id,
            dhcp_options_id=self._vcn.default_dhcp_options_id,
            opts=self._child_opts,
        )

    def _create_route_table(self):
        self._route_table = oci.core.DefaultRouteTable(
            compartment_id=self._compartment.id,
            resource_name=f"route_{self._instance_name}",
            route_rules=[
                oci.core.RouteTableRouteRuleArgs(
                    network_entity_id=self._internet_gateway.id,
                    destination="0.0.0.0/0",
                )
            ],
            manage_default_resource_id=self._subnet.route_table_id,
            opts=self._child_opts,
        )
        oci.core.RouteTableAttachment(
            resource_name=f"route_attachment_{self._instance_name}",
            subnet_id=self._subnet.id,
            route_table_id=self._route_table.id,
            opts=self._child_opts,
        )
