"""One bounded public-HTTPS request for a fixed manifest/signature/key resource."""
import http.client
import ipaddress
import re
import socket
import ssl
import sys
from urllib.parse import urlsplit
from pathlib import Path

# Direct script execution needs only the repository root; package imports need no path edits.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.common.origins import FetchError, normalize_origin, public_address

MAX_BYTES = 65536
SOCKET_TIMEOUT = 3
MANIFEST_PATH = "/.well-known/agent-trust.json"
RESOURCES = {
    "manifest": (MANIFEST_PATH, "application/json", MAX_BYTES),
    "signature": (MANIFEST_PATH + ".jws", "application/jose", 4096),
    "keys": ("/.well-known/agent-trust-keys.json", "application/json", 16384),
}


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


def fetch(origin, resolver=socket.getaddrinfo, connection=PinnedHTTPSConnection, resource="manifest"):
    if resource not in RESOURCES:
        raise FetchError("unsupported_resource")
    path, media_type, limit = RESOURCES[resource]
    origin = normalize_origin(origin)
    host = urlsplit(origin).hostname
    endpoints = resolver(host, 443, type=socket.SOCK_STREAM)
    if not endpoints or len(endpoints) > 16 or any(
            not public_address(item[4][0]) for item in endpoints):
        raise FetchError("unsafe_address")
    client = connection(host, endpoints[0])
    try:
        client.request("GET", path, headers={
            "Accept": media_type, "Accept-Encoding": "identity",
            "User-Agent": "atm-reference-consumer/0.1",
        })
        response = client.getresponse()
        if 300 <= response.status < 400:
            raise FetchError("redirect_rejected")
        if response.status == 404 and resource == "signature":
            raise FetchError("signature_absent")
        if response.status != 200:
            raise FetchError("http_failure")
        content_type = response.getheader("Content-Type", "").lower()
        if content_type.split(";", 1)[0].strip() != media_type:
            raise FetchError("unsupported_content_type")
        if response.getheader("Content-Encoding", "identity").lower() != "identity":
            raise FetchError("unsupported_encoding")
        lengths = [v for k, v in response.getheaders() if k.lower() == "content-length"]
        if len(lengths) > 1 or (lengths and response.getheader("Transfer-Encoding")):
            raise FetchError("ambiguous_length")
        if lengths:
            if not re.fullmatch(r"[0-9]+", lengths[0]) or len(lengths[0]) > 10:
                raise FetchError("ambiguous_length")
            if int(lengths[0]) > limit:
                raise FetchError("document_too_large")
        body = response.read(limit + 1)
        if len(body) > limit:
            raise FetchError("document_too_large")
        if lengths and len(body) != int(lengths[0]):
            raise FetchError("incomplete_body")
        return body
    finally:
        client.close()


if __name__ == "__main__":
    try:
        if len(sys.argv) not in (2, 3):
            raise FetchError("invalid_origin")
        sys.stdout.buffer.write(fetch(sys.argv[1], resource=sys.argv[2] if len(sys.argv) == 3 else "manifest"))
    except FetchError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
    except (OSError, ValueError, http.client.HTTPException):
        print("network_failure", file=sys.stderr)
        raise SystemExit(1)
