from pulumi_cloudflare import Record
from pulumi import Config

config = Config()


def create_dns_records(target_ip: str):
    for dns in config.require_object("cloudflare-record-names"):
        Record(
            f"{dns.get('name')}-record",
            name=dns.get("name"),
            zone_id=config.require("cloudflare-zone-id"),
            type="A",
            value=target_ip,
            allow_overwrite=True,
            proxied=dns.get("proxy"),
            ttl=1,
        )