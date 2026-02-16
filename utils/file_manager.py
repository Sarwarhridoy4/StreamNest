from __future__ import annotations

from pathlib import Path


def resolve_download_directory(path: str | None) -> tuple[str, bool]:
    """Returns normalized directory path and whether a fallback path was used."""
    fallback = (Path.home() / "Downloads").expanduser()
    target = Path(path).expanduser() if path else fallback

    try:
        target.mkdir(parents=True, exist_ok=True)
        return str(target.resolve()), False
    except OSError:
        fallback.mkdir(parents=True, exist_ok=True)
        return str(fallback.resolve()), True


def ensure_download_directory(path: str | None) -> str:
    """Ensures download directory exists and returns absolute path."""
    normalized, _ = resolve_download_directory(path)
    return normalized


def format_bytes(num_bytes: int | float | None) -> str:
    if not num_bytes or num_bytes <= 0:
        return "Unknown"

    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    unit = 0
    while size >= 1024 and unit < len(units) - 1:
        size /= 1024
        unit += 1
    return f"{size:.1f} {units[unit]}"


def format_speed(bytes_per_second: float | None) -> str:
    if not bytes_per_second or bytes_per_second <= 0:
        return ""
    return f"{format_bytes(bytes_per_second)}/s"


def format_eta(seconds: int | None) -> str:
    if seconds is None or seconds < 0:
        return ""

    mins, sec = divmod(int(seconds), 60)
    hrs, mins = divmod(mins, 60)

    if hrs > 0:
        return f"{hrs}h {mins}m {sec}s"
    if mins > 0:
        return f"{mins}m {sec}s"
    return f"{sec}s"
