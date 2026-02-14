from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yt_dlp


@dataclass
class QualityOption:
    label: str
    value: str
    height: int | None = None
    filesize: int | None = None


@dataclass
class MediaInfo:
    url: str
    title: str
    thumbnail: str
    is_playlist: bool
    options: list[QualityOption]


@dataclass
class PlaylistEntry:
    index: int
    title: str
    url: str
    duration: int | None = None


@dataclass
class PlaylistInfo:
    url: str
    title: str
    entries: list[PlaylistEntry]
    options: list[QualityOption]


class FormatExtractor:
    """Extracts media metadata and available quality options."""

    def __init__(self) -> None:
        self._base_opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": False,
            "extract_flat": False,
            "skip_download": True,
        }

    def extract(self, url: str) -> MediaInfo:
        with yt_dlp.YoutubeDL(self._base_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        is_playlist = info.get("_type") == "playlist" or bool(info.get("entries"))
        source = info

        if is_playlist:
            entries = info.get("entries") or []
            first_entry = next((entry for entry in entries if entry), None)
            if first_entry:
                source = first_entry

        title = info.get("title") or source.get("title") or "Untitled"
        thumbnail = source.get("thumbnail") or info.get("thumbnail") or ""

        return MediaInfo(
            url=url,
            title=title,
            thumbnail=thumbnail,
            is_playlist=is_playlist,
            options=self._build_quality_options(source),
        )

    def extract_playlist(self, url: str, items_expr: str | None = None) -> PlaylistInfo:
        opts = dict(self._base_opts)
        opts["extract_flat"] = "discard_in_playlist"
        opts["noplaylist"] = False
        if items_expr:
            opts["playlist_items"] = items_expr

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

        entries_raw = info.get("entries") or []
        entries: list[PlaylistEntry] = []
        first_entry_source: dict[str, Any] | None = None

        for idx, item in enumerate(entries_raw, start=1):
            if not isinstance(item, dict):
                continue
            item_url = item.get("webpage_url") or item.get("url")
            if not isinstance(item_url, str) or not item_url:
                continue

            if not item_url.startswith("http"):
                item_url = f"https://www.youtube.com/watch?v={item_url}"

            entry = PlaylistEntry(
                index=int(item.get("playlist_index") or idx),
                title=item.get("title") or f"Item {idx}",
                url=item_url,
                duration=item.get("duration") if isinstance(item.get("duration"), int) else None,
            )
            entries.append(entry)
            if first_entry_source is None:
                first_entry_source = item

        source_for_options = first_entry_source or info
        return PlaylistInfo(
            url=url,
            title=info.get("title") or "Playlist",
            entries=entries,
            options=self._build_quality_options(source_for_options),
        )

    def _build_quality_options(self, info: dict[str, Any]) -> list[QualityOption]:
        options: list[QualityOption] = [
            QualityOption(label="Best", value="best"),
            QualityOption(label="Worst", value="worst"),
        ]

        formats = info.get("formats") or []
        height_to_size: dict[int, int] = {}

        for item in formats:
            if not isinstance(item, dict):
                continue
            if item.get("vcodec") == "none":
                continue

            height = item.get("height")
            if not isinstance(height, int):
                continue

            if height < 144:
                continue

            filesize = item.get("filesize") or item.get("filesize_approx")
            prev = height_to_size.get(height)
            if isinstance(filesize, int):
                if prev is None or filesize > prev:
                    height_to_size[height] = filesize
            elif prev is None:
                height_to_size[height] = 0

        for height in sorted(height_to_size.keys()):
            selector = f"h{height}"
            options.append(
                QualityOption(
                    label=f"{height}p",
                    value=selector,
                    height=height,
                    filesize=height_to_size.get(height) or None,
                )
            )

        return options

    @staticmethod
    def resolve_format_selector(quality_value: str, mode: str) -> str:
        """Maps UI quality selection to yt-dlp format selector."""
        if mode == "audio":
            return "bestaudio/best"

        if quality_value == "worst":
            return "worst"

        if quality_value == "best":
            return "bestvideo*+bestaudio/best"

        if quality_value.startswith("h") and quality_value[1:].isdigit():
            height = int(quality_value[1:])
            return (
                f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/"
                f"best[height<={height}]"
            )

        return "bestvideo*+bestaudio/best"

    @staticmethod
    def normalize_playlist_range(expr: str) -> str:
        cleaned = (expr or "").replace(" ", "")
        if not cleaned:
            return ""

        tokens = cleaned.split(",")
        normalized: list[str] = []
        for token in tokens:
            if not token:
                continue
            if "-" in token:
                start_str, end_str = token.split("-", maxsplit=1)
                if not start_str.isdigit() or not end_str.isdigit():
                    raise ValueError("Invalid playlist range. Use values like 1-5 or 2,4,8-10.")
                start = int(start_str)
                end = int(end_str)
                if start <= 0 or end <= 0 or start > end:
                    raise ValueError("Playlist range values must be positive and ascending.")
                normalized.append(f"{start}-{end}")
            else:
                if not token.isdigit():
                    raise ValueError("Invalid playlist range. Use values like 1-5 or 2,4,8-10.")
                value = int(token)
                if value <= 0:
                    raise ValueError("Playlist range values must be positive.")
                normalized.append(str(value))

        return ",".join(normalized)
