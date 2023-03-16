from pulumi import Config
from pulumi_cloudflare import Record

config = Config()


def create_dns_records(target_ip: str):
    for dns in config.require_object("cloudflare_record_names"):
        Record(
            f"{dns.get('name')}-record",
            name=dns.get("name"),
            zone_id=config.require("cloudflare_zone_id"),
            type="A",
            value=target_ip,
            allow_overwrite=True,
            proxied=dns.get("proxy"),
            ttl=1,
        )
