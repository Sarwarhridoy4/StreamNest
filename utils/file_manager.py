from __future__ import annotations

import os
from pathlib import Path

# Maximum size in bytes for a single download (5 GB).
MAX_DOWNLOAD_SIZE = 5 * 1024 * 1024 * 1024

# Roots that user-provided paths are allowed to resolve within.
_ALLOWED_ROOTS: list[Path] = []


def _initialize_allowed_roots() -> list[Path]:
    """Populate the set of filesystem roots user paths may resolve within."""
    home = Path.home().resolve()
    tmp = Path(os.getenv("TMPDIR", "/tmp")).resolve()
    downloads = (home / "Downloads").resolve()
    roots = {home, tmp, downloads}
    return sorted(roots, key=str)


_ALLOWED_ROOTS: list[Path] = _initialize_allowed_roots()


def is_path_within_allowed_roots(path: Path) -> bool:
    """Return True when ``path`` resolves inside one of the allowed roots."""
    resolved = path.resolve()
    for root in _ALLOWED_ROOTS:
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        return True
    return False


def resolve_download_directory(path: str | None) -> tuple[str, bool]:
    """Returns normalized directory path and whether a fallback path was used."""
    fallback = (Path.home() / "Downloads").expanduser().resolve()
    target = Path(path).expanduser() if path else fallback

    try:
        target.mkdir(parents=True, exist_ok=True)
        resolved = target.resolve()
    except OSError:
        fallback.mkdir(parents=True, exist_ok=True)
        return str(fallback), True

    if not is_path_within_allowed_roots(resolved):
        fallback.mkdir(parents=True, exist_ok=True)
        return str(fallback), True

    return str(resolved), False


def ensure_download_directory(path: str | None) -> str:
    """Ensures download directory exists and returns absolute path."""
    normalized, _ = resolve_download_directory(path)
    return normalized


def format_bytes(num_bytes: float | None) -> str:
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


def is_download_size_allowed(num_bytes: float | None) -> bool:
    """Return True when the download size does not exceed the configured limit."""
    if num_bytes is None:
        return True
    return float(num_bytes) <= MAX_DOWNLOAD_SIZE
