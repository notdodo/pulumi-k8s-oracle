import pulumi_oci as oci


class Compartment:
    def create_compartment(self, config):
        try:
            return oci.identity.Compartment(
                "{}Compartment".format(config.get("prefix")),
                name="{}Compartment".format(config.get("prefix")),
                description="Compartment for the free instance",
                enable_delete=True,
            )
        except Exception as err:
            print("Error creating Compartement: ", str(err))
