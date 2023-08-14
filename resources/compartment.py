from typing import Optional

import pulumi
import pulumi_oci as oci


class Compartment(pulumi.ComponentResource):
    def __init__(
        self,
        name: str,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        super().__init__("oracle:Compartment", name, None, opts)
        self.__child_opts = pulumi.ResourceOptions(parent=self)
        self.compartment = self.__create_compartment(name)
        self.id = self.get_id()

    def __create_compartment(self, name: str) -> oci.identity.Compartment:
        return oci.identity.Compartment(
            "{}Compartment".format(name),
            name="{}Compartment".format(name),
            description="Compartment for the free tier",
            opts=self.__child_opts,
        )

    def get_id(self) -> str:
        return self.compartment.id
