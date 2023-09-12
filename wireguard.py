import pulumi

INTERFACE = """[Interface]
PrivateKey = {private_key}
Address = {interface}/32
ListenPort = 51000
"""

PEER = """[Peer]
PublicKey = {public_key}
Endpoint = {peer_ip}:51000
AllowedIPs = {allowed_ips}
"""


def generate_config(interface: str, private_key: str, peers: list) -> None:
    config = pulumi.Output.all(private_key=private_key).apply(
        lambda private_key: INTERFACE.format(
            private_key=private_key["private_key"], interface=interface
        )
    )
    for peer in peers:
        config = pulumi.Output.concat(
            config,
            pulumi.Output.all(
                public_key=peer.get("public_key"),
                peer_ip=peer.get("public_ip"),
            ).apply(
                lambda args: PEER.format(
                    public_key=args["public_key"],
                    peer_ip=args["peer_ip"],
                    allowed_ips=peer.get("allowed_ips"),
                )
            ),
        )

    return config
