import json

from fritzconnection import FritzConnection
from cloudflare import Cloudflare
from typing import Sequence


def get_ips_from_fritzbox(fritzbox_user_password: str) -> Sequence[str]:
    conn = FritzConnection("192.168.1.1", port=None, user= "user", password=fritzbox_user_password)
    ipv4 = conn.call_action("WANIPConn1", "GetExternalIPAddress")["NewExternalIPAddress"]
    ipv6 = conn.call_action("WANIPConn1", "X_AVM_DE_GetExternalIPv6Address")["NewExternalIPv6Address"]
    return ipv4, ipv6


def update_cloudflare_if_needed(client: Cloudflare, cloudflare_zone_id: str, ipv4: str, ipv6: str):
    for dns in client.dns.records.list(zone_id=cloudflare_zone_id):
        if dns.name == "luis.tg" and dns.type == "A" and ipv4 != dns.content:
            client.dns.records.update(dns.id, zone_id=cloudflare_zone_id, content=ipv4)
        if dns.name == "luis.tg" and dns.type == "AAAA" and ipv6 != dns.content:
            client.dns.records.update(dns.id, zone_id=cloudflare_zone_id, content=ipv6)


if __name__ == "__main__":
    with open(".config", "r+") as f:
        config = json.load(f)
        fritzbox_user_password = config["fritzbox_user_password"]
        cloudflare_zone_id = config["cloudflare_zone_id"]
        cloudflare_token = config["cloudflare_token"]
        old_ipv4, old_ipv6 = config["ipv4"], config["ipv6"]

        ipv4, ipv6 = get_ips_from_fritzbox(fritzbox_user_password)
        if ipv4 == old_ipv4 and ipv6 == old_ipv6:
            exit()

        client = Cloudflare(api_token=cloudflare_token)
        update_cloudflare_if_needed(client, cloudflare_zone_id, ipv4, ipv6)

        config["ipv4"], config["ipv6"] = ipv4, ipv6
        f.seek(0)
        json.dump(config, f, indent=4)
