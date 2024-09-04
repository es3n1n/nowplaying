import socket
from urllib.parse import urlparse


def try_resolve_hostname(hostname: str, port: int = 80) -> bool:
    try:
        socket.getaddrinfo(hostname, port)
    except (TimeoutError, socket.gaierror):
        return False
    else:
        return True


def try_resolve_url(url: str) -> bool:
    url_info = urlparse(url)

    hostname = url_info.netloc
    port_num = 80 if url_info.scheme == 'http' else 443

    if ':' in hostname.rstrip(':'):
        params = hostname.split(':', maxsplit=1)
        hostname = params[0]
        port_num = int(params[1])

    return try_resolve_hostname(hostname, port_num)


def select_hostname(docker_endpoint: str, fallback_endpoint: str, port: int = 80) -> str:
    if docker_endpoint == fallback_endpoint:
        return fallback_endpoint

    return docker_endpoint if try_resolve_hostname(docker_endpoint, port) else fallback_endpoint


def select_url(docker_endpoint: str, fallback_endpoint: str) -> str:
    if docker_endpoint == fallback_endpoint:
        return fallback_endpoint

    return docker_endpoint if try_resolve_url(docker_endpoint) else fallback_endpoint
