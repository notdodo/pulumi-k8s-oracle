from pulumi import Config
from pulumi_cloudflare import Record

config = Config()


def create_dns_records(target_ip: str, dns_record: dict):
    record_name = dns_record.get("name")
    proxy_enable = dns_record.get("proxy")
    if dns_record.get("proxy"):
        ttl = 1
    else:
        ttl = 60
    Record(
        f"{record_name}-cf-record",
        name=record_name,
        zone_id=config.require("cloudflare_zone_id"),
        type="A",
        value=target_ip,
        allow_overwrite=True,
        proxied=proxy_enable,
        ttl=ttl,
    )
