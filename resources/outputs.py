import pulumi


def outputs(oci_instance):
    pulumi.export("instance_ip", oci_instance.public_ip)
