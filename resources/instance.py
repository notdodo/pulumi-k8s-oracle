import base64
import pulumi_oci as oci
import pulumi


class Instance:
    __config = pulumi.Config()

    def __select_image(self, compartment):
        return (
            oci.core.get_images(
                compartment_id=compartment.id,
                operating_system=self.__config.get("instance_node_operating_system"),
                operating_system_version=self.__config.get(
                    "instance_operating_system_version"
                ),
                shape=self.__config.get("instance_node_shape"),
                sort_by="TIMECREATED",
                sort_order="DESC",
            )
            .images[0]
            .id
        )

    def __add_backup_policy(self, volume):
        oci.core.VolumeBackupPolicyAssignment(
            "VolumeBackupPolicyAssignment",
            asset_id=volume,
            policy_id=self.__config.get("backup_policy_id"),
        )

    def create_instaces(self, compartment, node_subnet):
        try:
            get_ad_name = oci.identity.get_availability_domain(
                compartment_id=self.__config.get("tenancyOcid"), ad_number=1
            )
            user_data_plain = open(self.__config.get("user_data")).read()
            user_data = base64.b64encode(bytes(user_data_plain, "utf-8")).decode(
                "utf-8"
            )
            ssh_pub_key = open(self.__config.require("path_ssh_pubkey"), "r").read()

            instance = oci.core.Instance(
                self.__config.get("instance_name"),
                instance_options=oci.core.InstanceConfigurationInstanceDetailsLaunchDetailsInstanceOptionsArgs(
                    are_legacy_imds_endpoints_disabled=True
                ),
                agent_config=oci.core.InstanceAgentConfigArgs(
                    plugins_configs=[
                        oci.core.InstanceAgentConfigPluginsConfigArgs(
                            desired_state=self.__config.require(
                                "oci_agent_vulnerability"
                            ),
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
                            desired_state=self.__config.require(
                                "oci_agent_comptinstance"
                            ),
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
                ),
                availability_domain=get_ad_name.__dict__["name"],
                compartment_id=compartment.id,
                create_vnic_details=oci.core.InstanceCreateVnicDetailsArgs(
                    subnet_id=node_subnet.id,
                    assign_public_ip=self.__config.get("public_ip_enabled"),
                ),
                display_name=self.__config.require("instance_name"),
                fault_domain="FAULT-DOMAIN-1",
                metadata={
                    "user_data": user_data,
                    "ssh_authorized_keys": ssh_pub_key,
                },
                shape=self.__config.require("instance_node_shape"),
                shape_config=oci.core.InstanceShapeConfigArgs(
                    memory_in_gbs=self.__config.require("instance_node_memory_in_gbs"),
                    ocpus=self.__config.require("instance_node_ocpus"),
                ),
                source_details=oci.core.InstanceSourceDetailsArgs(
                    source_id=self.__select_image(compartment),
                    source_type="image",
                    boot_volume_size_in_gbs="200",
                ),
            )

            self.__add_backup_policy(instance.boot_volume_id)
            return instance
        except Exception as error:
            print("Instance creation failed " + str(error))
