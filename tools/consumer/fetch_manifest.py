"""One bounded public-HTTPS manifest request; no redirects, proxies or evidence fetches."""
import http.client
import ipaddress
import re
import socket
import ssl
import sys
from urllib.parse import urlsplit

MAX_BYTES = 65536
SOCKET_TIMEOUT = 3
MANIFEST_PATH = "/.well-known/agent-trust.json"


class FetchError(Exception):
    pass


def normalize_origin(value):
    if not isinstance(value, str) or len(value) > 256 or not value.isascii():
        raise FetchError("invalid_origin")
    if any(ord(c) <= 32 or ord(c) == 127 for c in value):
        raise FetchError("invalid_origin")
    try:
        parts = urlsplit(value)
        host = parts.hostname
        if (parts.scheme != "https" or not host or parts.username is not None
                or parts.password is not None or parts.port not in (None, 443)
                or parts.path not in ("", "/") or parts.query or parts.fragment
                or "?" in value or "#" in value or "%" in host):
            raise ValueError()
        try:
            address = ipaddress.ip_address(host)
            host = address.compressed
            if not public_address(host):
                raise ValueError()
        except ValueError:
            if not re.fullmatch(r"(?=.{1,253}$)[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", host):
                raise ValueError()
            labels = host.split(".")
            if len(labels) < 2 or any(not label or len(label) > 63
                    or label.startswith("-") or label.endswith("-") for label in labels):
                raise ValueError()
            # An IP literal failing the public-address check must not become a hostname.
            if re.fullmatch(r"[0-9.]+", host):
                raise ValueError()
    except (ValueError, TypeError):
        raise FetchError("invalid_origin") from None
    authority = "[" + host + "]" if ":" in host else host
    return "https://" + authority


def public_address(value):
    try:
        address = ipaddress.ip_address(value)
        if isinstance(address, ipaddress.IPv6Address) and (
                address.ipv4_mapped is not None or address.sixtofour is not None
                or address.teredo is not None):
            return False
        return (address.is_global and not address.is_multicast and not address.is_reserved
                and not address.is_loopback and not address.is_link_local
                and not address.is_unspecified)
    except ValueError:
        return False


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, hostname, endpoint):
        context = ssl.create_default_context()
        context.set_alpn_protocols(["http/1.1"])
        super().__init__(hostname, port=443, timeout=SOCKET_TIMEOUT,
                         context=context)
        self.endpoint = endpoint

    def connect(self):
        family, socktype, protocol, _, sockaddr = self.endpoint
        raw = socket.socket(family, socktype, protocol)
        try:
            raw.settimeout(self.timeout)
            raw.connect(sockaddr)
            peer = raw.getpeername()[0]
            if not public_address(peer) or ipaddress.ip_address(peer) != ipaddress.ip_address(sockaddr[0]):
                raise FetchError("unsafe_address")
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except BaseException:
            raw.close()
            raise


def fetch(origin, resolver=socket.getaddrinfo, connection=PinnedHTTPSConnection):
    origin = normalize_origin(origin)
    host = urlsplit(origin).hostname
    endpoints = resolver(host, 443, type=socket.SOCK_STREAM)
    if not endpoints or len(endpoints) > 16 or any(
            not public_address(item[4][0]) for item in endpoints):
        raise FetchError("unsafe_address")
    client = connection(host, endpoints[0])
    try:
        client.request("GET", MANIFEST_PATH, headers={
            "Accept": "application/json", "Accept-Encoding": "identity",
            "User-Agent": "atm-reference-consumer/0.1",
        })
        response = client.getresponse()
        if 300 <= response.status < 400:
            raise FetchError("redirect_rejected")
        if response.status != 200:
            raise FetchError("http_failure")
        content_type = response.getheader("Content-Type", "").lower()
        if content_type.split(";", 1)[0].strip() != "application/json":
            raise FetchError("unsupported_content_type")
        if response.getheader("Content-Encoding", "identity").lower() != "identity":
            raise FetchError("unsupported_encoding")
        lengths = [v for k, v in response.getheaders() if k.lower() == "content-length"]
        if len(lengths) > 1 or (lengths and response.getheader("Transfer-Encoding")):
            raise FetchError("ambiguous_length")
        if lengths:
            if not re.fullmatch(r"[0-9]+", lengths[0]) or len(lengths[0]) > 10:
                raise FetchError("ambiguous_length")
            if int(lengths[0]) > MAX_BYTES:
                raise FetchError("document_too_large")
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise FetchError("document_too_large")
        return body
    finally:
        client.close()


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise FetchError("invalid_origin")
        sys.stdout.buffer.write(fetch(sys.argv[1]))
    except FetchError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
    except (OSError, ValueError, http.client.HTTPException):
        print("network_failure", file=sys.stderr)
        raise SystemExit(1)
