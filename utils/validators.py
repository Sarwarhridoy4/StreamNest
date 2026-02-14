from __future__ import annotations

import re
from urllib.parse import urlparse


YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
}


def is_valid_url(url: str) -> bool:
    """Basic URL validation to avoid unnecessary extractor calls."""
    if not url or not url.strip():
        return False

    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    if not parsed.netloc:
        return False

    return True


def is_youtube_url(url: str) -> bool:
    if not is_valid_url(url):
        return False

    host = urlparse(url.strip()).netloc.lower()
    return host in YOUTUBE_HOSTS


def sanitize_filename_component(value: str) -> str:
    """Removes reserved characters from a custom filename/path fragment."""
    cleaned = re.sub(r'[\\/:*?"<>|]+', "_", value).strip()
    return cleaned or "download"
