import importlib.util
import ipaddress
import socket
from urllib.parse import urlparse


class DownloadError(Exception):
    def __init__(self, code, **kwargs):
        super().__init__(code)
        self.code = code
        self.kwargs = kwargs


def has_module(name):
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def validate_url(value):
    try:
        parsed = urlparse(value.strip())
        return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)
    except ValueError:
        return False


def get_network_interfaces():
    if not has_module("psutil"):
        return []
    import psutil

    excluded = ("loopback", "vethernet", "hyper-v", "docker", "vmware", "virtualbox", "tailscale", "wireguard", "tap", "wintun")
    stats = psutil.net_if_stats()
    result = []
    for name, addresses in psutil.net_if_addrs().items():
        lowered = name.lower()
        if any(token in lowered for token in excluded):
            continue
        if not stats.get(name) or not stats[name].isup:
            continue
        for address in addresses:
            if address.family != socket.AF_INET:
                continue
            try:
                ip = ipaddress.ip_address(address.address)
            except ValueError:
                continue
            if not ip.is_loopback and not ip.is_link_local:
                result.append({"name": name, "ip": address.address})
                break
    return result


def get_file_info(url):
    if not has_module("requests"):
        raise DownloadError("missing_requests")
    import requests

    headers = {"Range": "bytes=0-0", "Accept-Encoding": "identity", "User-Agent": "MultiNIC-Downloader/1.0"}
    with requests.get(url, headers=headers, allow_redirects=True, stream=True, timeout=(15, 30)) as response:
        response.raise_for_status()
        if response.status_code != 206:
            raise DownloadError("range_not_supported")
        content_range = response.headers.get("Content-Range", "")
        try:
            unit, values = content_range.split(" ", 1)
            received, total = values.split("/", 1)
            start, end = (int(value) for value in received.split("-", 1))
            size = int(total)
        except (ValueError, AttributeError):
            raise DownloadError("invalid_content_range") from None
        if unit.lower() != "bytes" or start != 0 or end != 0 or size <= 0:
            raise DownloadError("range_mismatch")
        return {"size": size, "final_url": response.url}


def split_ranges(total_size, count):
    if total_size <= 0 or count <= 0:
        return []
    count = min(count, total_size)
    base, extra = divmod(total_size, count)
    start = 0
    ranges = []
    for index in range(count):
        length = base + (1 if index < extra else 0)
        end = start + length - 1
        ranges.append((start, end))
        start = end + 1
    return ranges


def make_bound_session(source_ip):
    import requests
    from requests.adapters import HTTPAdapter

    class SourceAddressAdapter(HTTPAdapter):
        def init_poolmanager(self, connections, maxsize, block=False, **kwargs):
            kwargs["source_address"] = (source_ip, 0)
            return super().init_poolmanager(connections, maxsize, block=block, **kwargs)

        def proxy_manager_for(self, *args, **kwargs):
            raise DownloadError("env_proxy_not_supported")

    session = requests.Session()
    session.trust_env = False
    adapter = SourceAddressAdapter(pool_connections=1, pool_maxsize=1, max_retries=0)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session