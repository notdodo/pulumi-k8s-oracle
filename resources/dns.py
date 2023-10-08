from pulumi import Config, ResourceOptions
from pulumi_cloudflare import Record

config = Config()


def create_dns_records(
    target_name: str, target_ip: str, dns_record: dict, deps: ResourceOptions = []
):
    record_name = dns_record.get("name")
    if dns_record.get("proxy"):
        ttl = 1
    else:
        ttl = 60
    Record(
        f"{record_name}-cf-record_{target_name}",
        name=record_name,
        zone_id=config.require("cloudflare_zone_id"),
        type=dns_record.get("type"),
        value=target_ip,
        allow_overwrite=True,
        proxied=dns_record.get("proxy"),
        ttl=ttl,
        opts=ResourceOptions(depends_on=deps),
    )
