import pulumi


def outputs(oci_instance):
    pulumi.export("Stack", "K8S with Pulumi on Oracle FreeTier")
    pulumi.export("Instance PublicIP", oci_instance.public_ip)
