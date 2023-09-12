from typing import Optional

import pulumi
import pulumi_oci as oci


class Compartment(pulumi.ComponentResource):
    def __init__(
        self,
        compartment_name: str,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        super().__init__("oracle:Compartment", compartment_name, None, opts)
        self._child_opts = pulumi.ResourceOptions(parent=self)
        self._compartment = self.__create_compartment(compartment_name)

    def __create_compartment(self, name: str) -> oci.identity.Compartment:
        return oci.identity.Compartment(
            f"compartment_{name}",
            name=f"compartment_{name}",
            description="Compartment for the free tier",
            opts=self._child_opts,
        )

    @property
    def id(self):
        return self._compartment.id
