from pulumi import ResourceOptions
import pulumi_oci as oci


class Compartment:
    id = ""

    def __init__(self, id) -> None:
        self.id = id

    def create_compartment(self, config):
        try:
            return oci.identity.Compartment(
                "{}Compartment".format(config.get("prefix")),
                name="{}Compartment".format(config.get("prefix")),
                description="Compartment for the free instance",
            )
        except Exception as err:
            print("Error creating Compartement: ", str(err))
