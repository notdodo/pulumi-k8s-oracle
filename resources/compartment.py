import pulumi_oci as oci
import pulumi

from typing import Optional


class Compartment(pulumi.ComponentResource):
    def __init__(
        self,
        props: Optional[pulumi.Inputs] = None,
        opts: Optional[pulumi.ResourceOptions] = None,
        remote: bool = False,
    ) -> None:
        self.__config = pulumi.Config()
        super().__init__("oracle:Compartment", self.__config.get("prefix"), None, opts)
        self.__child_opts = pulumi.ResourceOptions(parent=self)
        self.compartment = self.__create_compartment()
        self.id = self.get_id()

    def __create_compartment(self) -> oci.identity.Compartment:
        return oci.identity.Compartment(
            "{}Compartment".format(self.__config.get("prefix")),
            name="{}Compartment".format(self.__config.get("prefix")),
            description="Compartment for the free tier",
            opts=self.__child_opts,
        )

    def get_id(self) -> str:
        return self.compartment.id
