import pulumi  # pyright: reportShadowedImports=false
import pulumi_oci as oci

free_compartment = oci.identity.Compartment(
    "AlwaysFree",
    description="AlwaysFree Compartment for the free instance",
    freeform_tags={
        "Name": "AlwaysFree",
    },
)

free_vnc = oci.core.Vcn(
    compartment_id=free_compartment.id,
    resource_name="AlwaysFreeVcn",
    cidr_block="10.0.0.0/24",
    display_name="AlwaysFreeVcn",
)

free_vnc_security_list = oci.core.SecurityList(
    compartment_id=free_compartment.compartment_id,
    resource_name="AlwaysFreeSecurityList",
    vcn_id=free_vnc.id,
    display_name="AlwaysFreeSecurityList",
    egress_security_rules=[
        oci.core.SecurityListEgressSecurityRuleArgs(
            protocol="all",
            destination="0.0.0.0/0",
            description="Allow all outbound traffic",
        )
    ],
    ingress_security_rules=[
        oci.core.SecurityListIngressSecurityRuleArgs(
            protocol="all",
            source="0.0.0.0/0",
            description="YOLO",
        )
    ],
)

free_vnc_subnet1 = oci.core.Subnet(
    compartment_id=free_compartment.id,
    resource_name="AlwaysFreeSubnet1",
    vcn_id=free_vnc.id,
    cidr_block="10.0.0.0/24",
    display_name="AlwaysFreeSubnet1",
    security_list_ids=[
        free_vnc.default_security_list_id,
        free_vnc_security_list.id,
    ],
    prohibit_public_ip_on_vnic=False,
    route_table_id=free_vnc.default_route_table_id,
    dhcp_options_id=free_vnc.default_dhcp_options_id,
)
