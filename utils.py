import ipaddress

def is_telegram_ip(ip: str) -> bool:
    allowed_subnets = [
        ipaddress.ip_network("149.154.160.0/20"),
        ipaddress.ip_network("91.108.4.0/22")
    ]
    try:
        ip = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(ip in subnet for subnet in allowed_subnets)