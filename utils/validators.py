from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

# Maximum total URL length.
MAX_URL_LENGTH = 2048
# Maximum hostname length per RFC 1035.
MAX_HOSTNAME_LENGTH = 253
# Ports that are never allowed (privileged/dangerous common ports).
BLOCKED_PORTS = {
    20, 21, 22, 23, 25, 53, 69, 110, 111, 135, 139, 143,
    161, 389, 445, 587, 993, 995, 1433, 3306, 3389, 5432,
    5900, 6379, 8080, 8443, 27017,
}
# Suspicious path fragments that may indicate path traversal or injection.
SUSPICIOUS_PATH_PATTERNS = [
    re.compile(r"\.\.", re.IGNORECASE),
    re.compile(r"%2e%2e", re.IGNORECASE),
    re.compile(r"%252e%252e", re.IGNORECASE),
    re.compile(r"/etc/", re.IGNORECASE),
    re.compile(r"/proc/", re.IGNORECASE),
    re.compile(r"/sys/", re.IGNORECASE),
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"data:", re.IGNORECASE),
]


def is_valid_url(url: str) -> bool:
    """Validate only safe/public HTTP(S) URLs."""
    if not url or not url.strip():
        return False

    normalized = url.strip()
    if len(normalized) > MAX_URL_LENGTH:
        return False

    # Block credentials embedded anywhere in the URL string.
    if "@" in normalized:
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

    # Block suspicious path/query fragments.
    full_path = (parsed.path or "") + (parsed.query or "")
    for pattern in SUSPICIOUS_PATH_PATTERNS:
        if pattern.search(full_path):
            return False

    hostname = parsed.hostname
    if not hostname:
        return False

    if len(hostname) > MAX_HOSTNAME_LENGTH:
        return False

    hostname_lower = hostname.lower()
    if hostname_lower == "localhost" or hostname_lower.endswith(".local"):
        return False

    # Block numeric IP addresses that are private/loopback/reserved.
    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        ip = None

    if ip and (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_unspecified
        or ip.is_multicast
    ):
        return False

    # Block dangerous port numbers.
    return not (parsed.port is not None and parsed.port in BLOCKED_PORTS)


def sanitize_filename_component(value: str) -> str:
    """Removes reserved characters from a custom filename/path fragment."""
    cleaned = re.sub(r'[\\/:*?"<>|]+', "_", value).strip()
    # Collapse multiple underscores and leading/trailing dots/spaces.
    cleaned = re.sub(r"_+", "_", cleaned).strip("_ .")
    return cleaned or "download"
