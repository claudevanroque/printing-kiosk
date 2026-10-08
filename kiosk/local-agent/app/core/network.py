
import ipaddress
import socket

import psutil


def get_ipv4_interfaces() -> list[dict]:
    interfaces = []
    stats = psutil.net_if_stats()

    for name, addresses in psutil.net_if_addrs().items():
        status = stats.get(name)

        if not status or not status.isup:
            continue

        for address in addresses:
            if address.family != socket.AF_INET:
                continue

            ip = ipaddress.ip_address(address.address)

            if ip.is_loopback or ip.is_link_local:
                continue

            interfaces.append({
                "name": name,
                "ip": str(ip),
                "netmask": address.netmask,
            })

    return interfaces


def get_hotspot_ip() -> str | None:
    interfaces = get_ipv4_interfaces()

    candidates = []

    for interface in interfaces:
        name = interface["name"].lower()
        ip = interface["ip"]

        is_hotspot_adapter = any(
            keyword in name
            for keyword in (
                "local area connection*",
                "wi-fi direct",
                "mobile hotspot",
                "microsoft wi-fi direct",
            )
        )

        if is_hotspot_adapter or ip == "192.168.137.1":
            candidates.append(ip)

    candidates = list(set(candidates))

    if len(candidates) == 1:
        return candidates[0]

    return None


def get_upload_base_url(port: int = 9001) -> str:
    ip = get_hotspot_ip()

    if ip is None:
        return None

    return f"http://{ip}:{port}"

print(get_upload_base_url())

# if __name__ == "__main__":
#     from pprint import pprint

#     print("Available network interfaces:")
#     pprint(get_ipv4_interfaces())

#     print("\nDetected hotspot IP:")
#     print(get_hotspot_ip())

#     try:
#         print("\nUpload URL:")
#         print(get_upload_base_url())
#     except RuntimeError as error:
#         print(error)
