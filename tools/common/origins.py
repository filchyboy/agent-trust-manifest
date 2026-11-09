"""Shared offline origin and public-address rules; performs no network requests."""
import ipaddress
import re
from urllib.parse import urlsplit


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
