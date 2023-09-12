import os
import stat
from pathlib import Path

import pulumi_tls


def generate_ssh_keys(path: str = "./"):
    path = Path(path).resolve()

    if not (
        os.path.exists(path / "ssh_priv.key") and os.path.exists(path / "ssh_pub.key")
    ):
        private_key_resource = pulumi_tls.PrivateKey(
            "k8sPrivateKey",
            algorithm="ED25519",
        )
        public_key = private_key_resource.public_key_openssh
        private_key = private_key_resource.private_key_openssh

        def write_to_file(what, file):
            with open(file, "w") as f:
                f.write(what)
            os.chmod(file, stat.S_IRWXU)

        private_key.apply(lambda x: write_to_file(x, path / "ssh_priv.key"))
        public_key.apply(lambda x: write_to_file(x, path / "ssh_pub.key"))
    else:
        private_key = open(path / "ssh_pub.key").read()
        public_key = open(path / "ssh_pub.key").read()
    return private_key, public_key
