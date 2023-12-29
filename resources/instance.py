from typing import Optional

import pulumi
import pulumi_oci as oci

from resources.compartment import Compartment
from resources.network import Network


class Instance(pulumi.ComponentResource):
    def __init__(
        self,
        name: str,
        compartment: Compartment,
        network: Network,
        user_data: Optional[str],
        private_ip: Optional[str],
        public_ip_id: Optional[str],
        public_key: str,
        provider: Optional[pulumi.ProviderResource] = None,
        props: Optional[pulumi.Inputs] = None,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        self._config = pulumi.Config()
        super().__init__(
            "oracle:instance",
            name,
            props,
            opts,
        )
        self._child_opts = pulumi.ResourceOptions(
            parent=self,
            depends_on=[compartment, network],
            delete_before_replace=True,
            provider=provider,
        )
        self._compartment = compartment
        self._network = network
        self._private_ip = private_ip
        self._public_ip_id = public_ip_id
        self._provider = provider
        self._public_key = public_key
        self._resource_name = name
        self._user_data = user_data

    def _get_latest_image(
        self, instance_operating_system: str, instance_operating_system_version: str
    ):
        return (
            oci.core.get_images(
                compartment_id=self._config.require_secret(
                    f"{self._resource_name}_tenancy_ocid"
                ),
                operating_system=instance_operating_system,
                operating_system_version=instance_operating_system_version,
                sort_by="TIMECREATED",
                sort_order="DESC",
                opts=pulumi.InvokeOptions(provider=self._provider),
            )
            .images[0]
            .id
        )

    def _add_backup_policy(self):
        policy = oci.core.VolumeBackupPolicy(
            f"{self._resource_name}_backup_policy",
            compartment_id=self._compartment.id,
            display_name=f"{self._resource_name}_backup_policy",
            schedules=[
                oci.core.VolumeBackupPolicyScheduleArgs(
                    backup_type="FULL",
                    period="ONE_WEEK",
                    retention_seconds="604800",
                ),
            ],
            opts=self._child_opts,
        )
        oci.core.VolumeBackupPolicyAssignment(
            f"{self._resource_name}_backup_policy_assignment",
            asset_id=self._instance.boot_volume_id,
            policy_id=policy,
            opts=self._child_opts,
        )

    def _agent_config(self):
        return oci.core.InstanceAgentConfigArgs(
            plugins_configs=[
                oci.core.InstanceAgentConfigPluginsConfigArgs(
                    desired_state=self._config.require("oci_agent_vulnerability"),
                    name="Vulnerability Scanning",
                ),
                oci.core.InstanceAgentConfigPluginsConfigArgs(
                    desired_state=self._config.require("oci_agent_osmgmtsvc"),
                    name="OS Management Service Agent",
                ),
                oci.core.InstanceAgentConfigPluginsConfigArgs(
                    desired_state=self._config.require("oci_agent_mgmt"),
                    name="Management Agent",
                ),
                oci.core.InstanceAgentConfigPluginsConfigArgs(
                    desired_state=self._config.require("oci_agent_customlogs"),
                    name="Custom Logs Monitoring",
                ),
                oci.core.InstanceAgentConfigPluginsConfigArgs(
                    desired_state=self._config.require("oci_agent_comptinstance"),
                    name="Compute Instance Run Command",
                ),
                oci.core.InstanceAgentConfigPluginsConfigArgs(
                    desired_state=self._config.require(
                        "oci_agent_comptinstancemonitoring"
                    ),
                    name="Compute Instance Monitoring",
                ),
                oci.core.InstanceAgentConfigPluginsConfigArgs(
                    desired_state=self._config.require("oci_agent_blkvolume"),
                    name="Block Volume Management",
                ),
                oci.core.InstanceAgentConfigPluginsConfigArgs(
                    desired_state=self._config.require("oci_agent_bastion"),
                    name="Bastion",
                ),
            ],
        )

    def _generate_user_data(self, extra_cmds: list = [], substitutions: dict = {}):
        user_data_plain = self._user_data

        for k, v in substitutions.items():
            user_data_plain = user_data_plain.replace(k, v)

        for cmd in extra_cmds:
            user_data_plain = pulumi.Output.format("{}  - {}\n", user_data_plain, cmd)

        return pulumi.Output.from_input(user_data_plain)

    def create_instance(self) -> oci.core.Instance:
        self._instance = oci.core.Instance(
            f"instance_{self._resource_name}",
            instance_options=oci.core.InstanceConfigurationInstanceDetailsLaunchDetailsInstanceOptionsArgs(
                are_legacy_imds_endpoints_disabled=True
            ),
            agent_config=self._agent_config(),
            availability_domain=oci.identity.get_availability_domain(
                compartment_id=self._config.require_secret(
                    f"{self._resource_name}_tenancy_ocid"
                ),
                ad_number=1,
                opts=pulumi.InvokeOptions(provider=self._provider),
            ).__dict__["name"],
            compartment_id=self._compartment.id,
            create_vnic_details=oci.core.InstanceCreateVnicDetailsArgs(
                subnet_id=self._network.subnet.id,
                assign_public_ip=False,
                private_ip=self._private_ip,
            ),
            display_name=self._resource_name,
            metadata={
                "user_data": self._user_data,
                "ssh_authorized_keys": self._public_key,
            },
            shape=self._config.require("instance_shape"),
            shape_config=oci.core.InstanceShapeConfigArgs(
                memory_in_gbs=self._config.require("instance_memory_in_gbs"),
                ocpus=self._config.require("instance_ocpus"),
            ),
            source_details=oci.core.InstanceSourceDetailsArgs(
                source_id=self._get_latest_image(
                    instance_operating_system=self._config.require(
                        "instance_operating_system"
                    ),
                    instance_operating_system_version=self._config.require(
                        "instance_operating_system_version"
                    ),
                ),
                source_type="image",
                boot_volume_size_in_gbs=self._config.require("instance_volume_in_gbs"),
            ),
            opts=self._child_opts,
        )

        import pulumi_command as pc

        def assing_public_ip(instance_id):
            private_ip = oci.core.get_private_ips(
                ip_address=self._private_ip,
                subnet_id=self._network.subnet.id,
                opts=pulumi.InvokeOptions(
                    parent=self._instance, provider=self._provider
                ),
            ).private_ips[0]
            cmd = pulumi.Output.concat(
                "oci ",
                "network ",
                "public-ip ",
                "update ",
                "--public-ip-id ",
                self._public_ip_id,
                " --private-ip-id ",
                private_ip.id,
                " --profile ",
                self._provider._name,
            )
            pc.local.Command(
                f"assign_public_ip_{self._resource_name}",
                triggers=[instance_id],
                create=cmd,
                update=cmd,
                opts=pulumi.ResourceOptions(
                    parent=self._instance, depends_on=[self._instance]
                ),
            )

        self._instance.id.apply(lambda id: assing_public_ip(id))
        self._add_backup_policy()
        return self._instance
