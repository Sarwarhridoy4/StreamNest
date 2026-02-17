from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """Validate only safe/public HTTP(S) URLs."""
    if not url or not url.strip():
        return False

    normalized = url.strip()
    if len(normalized) > 2048:
        return False

    try:
        parsed = urlparse(normalized)
    except ValueError:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    if not parsed.netloc:
        return False

    if parsed.username or parsed.password:
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    if hostname.lower() == "localhost" or hostname.lower().endswith(".local"):
        return False

    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        ip = None

    if ip and (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_unspecified):
        return False

    return True


def sanitize_filename_component(value: str) -> str:
    """Removes reserved characters from a custom filename/path fragment."""
    cleaned = re.sub(r'[\\/:*?"<>|]+', "_", value).strip()
    return cleaned or "download"
