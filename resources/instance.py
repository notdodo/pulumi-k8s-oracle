import base64
from typing import Optional

import pulumi
import pulumi_oci as oci

from resources.compartment import Compartment
from resources.network import Network


class Instance(pulumi.ComponentResource):
    def __init__(
        self,
        compartment: Compartment,
        network: Network,
        props: Optional[pulumi.Inputs] = None,
        opts: Optional[pulumi.ResourceOptions] = None,
        remote: bool = False,
    ) -> None:
        self.__config = pulumi.Config()
        super().__init__(
            "oracle:instance", self.__config.get("instance_name"), props, opts, remote
        )
        self.__child_opts = pulumi.ResourceOptions(
            parent=self, depends_on=[compartment, network]
        )
        self.__compartment = compartment
        self.__network = network

    def __select_image(self) -> str:
        return (
            oci.core.get_images(
                compartment_id=self.__config.get("tenancyOcid"),
                operating_system=self.__config.require(
                    "instance_node_operating_system"
                ),
                operating_system_version=self.__config.require(
                    "instance_operating_system_version"
                ),
                shape=self.__config.require("instance_node_shape"),
                sort_by="TIMECREATED",
                sort_order="DESC",
            )
            .images[0]
            .id
        )

    def __add_backup_policy(self):
        policy = oci.core.VolumeBackupPolicy(
            "FreeBackupPolicy",
            compartment_id=self.__compartment.id,
            display_name="FreeBackupPolicy",
            schedules=[
                oci.core.VolumeBackupPolicyScheduleArgs(
                    backup_type="FULL",
                    period="ONE_WEEK",
                    retention_seconds="604800",
                ),
            ],
            opts=self.__child_opts,
        )
        oci.core.VolumeBackupPolicyAssignment(
            "VolumeBackupPolicyAssignment",
            asset_id=self.instance.boot_volume_id,
            policy_id=policy,
            opts=self.__child_opts,
        )

    def __agent_config(self):
        return oci.core.InstanceAgentConfigArgs(
            plugins_configs=[
                oci.core.InstanceAgentConfigPluginsConfigArgs(
                    desired_state=self.__config.require("oci_agent_vulnerability"),
                    name="Vulnerability Scanning",
                ),
                oci.core.InstanceAgentConfigPluginsConfigArgs(
                    desired_state=self.__config.require("oci_agent_osmgmtsvc"),
                    name="OS Management Service Agent",
                ),
                oci.core.InstanceAgentConfigPluginsConfigArgs(
                    desired_state=self.__config.require("oci_agent_mgmt"),
                    name="Management Agent",
                ),
                oci.core.InstanceAgentConfigPluginsConfigArgs(
                    desired_state=self.__config.require("oci_agent_customlogs"),
                    name="Custom Logs Monitoring",
                ),
                oci.core.InstanceAgentConfigPluginsConfigArgs(
                    desired_state=self.__config.require("oci_agent_comptinstance"),
                    name="Compute Instance Run Command",
                ),
                oci.core.InstanceAgentConfigPluginsConfigArgs(
                    desired_state=self.__config.require(
                        "oci_agent_comptinstancemonitoring"
                    ),
                    name="Compute Instance Monitoring",
                ),
                oci.core.InstanceAgentConfigPluginsConfigArgs(
                    desired_state=self.__config.require("oci_agent_blkvolume"),
                    name="Block Volume Management",
                ),
                oci.core.InstanceAgentConfigPluginsConfigArgs(
                    desired_state=self.__config.require("oci_agent_bastion"),
                    name="Bastion",
                ),
            ],
        )

    def create_instance(self):
        get_ad_name = oci.identity.get_availability_domain(
            compartment_id=self.__config.get("tenancyOcid"), ad_number=1
        )

        user_data_plain = open(self.__config.get("user_data")).read()

        user_data = base64.b64encode(bytes(user_data_plain, "utf-8")).decode("utf-8")

        ssh_pub_key = open(self.__config.require("path_ssh_pubkey"), "r").read()

        self.instance = oci.core.Instance(
            self.__config.get("instance_name"),
            instance_options=oci.core.InstanceConfigurationInstanceDetailsLaunchDetailsInstanceOptionsArgs(
                are_legacy_imds_endpoints_disabled=True
            ),
            agent_config=self.__agent_config(),
            availability_domain=get_ad_name.__dict__["name"],
            compartment_id=self.__compartment.id,
            create_vnic_details=oci.core.InstanceCreateVnicDetailsArgs(
                subnet_id=self.__network.get_subnet().id,
                assign_public_ip=self.__config.require_bool("public_ip_enabled"),
            ),
            display_name=self.__config.require("instance_name"),
            fault_domain="FAULT-DOMAIN-1",
            metadata={
                "user_data": user_data,
                "ssh_authorized_keys": ssh_pub_key,
            },
            shape=self.__config.require("instance_node_shape"),
            shape_config=oci.core.InstanceShapeConfigArgs(
                memory_in_gbs=self.__config.require_int("instance_node_memory_in_gbs"),
                ocpus=self.__config.require_int("instance_node_ocpus"),
            ),
            source_details=oci.core.InstanceSourceDetailsArgs(
                source_id=self.__select_image(),
                source_type="image",
                boot_volume_size_in_gbs=self.__config.require_int(
                    "instance_volume_in_gbs"
                ),
            ),
            opts=self.__child_opts,
        )

        self.__add_backup_policy()
        return self.instance
