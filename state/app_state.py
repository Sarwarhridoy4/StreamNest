from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock


@dataclass
class HistoryEntry:
    id: str
    timestamp: str
    title: str
    url: str
    platform: str
    mode: str
    quality: str
    save_directory: str
    context: str
    status: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "title": self.title,
            "url": self.url,
            "platform": self.platform,
            "mode": self.mode,
            "quality": self.quality,
            "save_directory": self.save_directory,
            "context": self.context,
            "status": self.status,
            "message": self.message,
        }

    @staticmethod
    def from_dict(data: dict[str, str]) -> HistoryEntry:
        return HistoryEntry(
            id=str(data.get("id", "")),
            timestamp=str(data.get("timestamp", "")),
            title=str(data.get("title", "")),
            url=str(data.get("url", "")),
            platform=str(data.get("platform", "Unknown")),
            mode=str(data.get("mode", "")),
            quality=str(data.get("quality", "")),
            save_directory=str(data.get("save_directory", "")),
            context=str(data.get("context", "single")),
            status=str(data.get("status", "success")),
            message=str(data.get("message", "")),
        )


@dataclass
class AppState:
    """Shared app state container used by the UI layer."""

    url: str = ""
    selected_mode: str = "video"  # video | playlist | audio
    selected_quality: str = "best"
    save_directory: str = ""
    playlist_save_directory: str = ""
    is_downloading: bool = False
    is_fetching_formats: bool = False
    progress: float = 0.0
    status_text: str = "Idle"
    speed_text: str = ""
    eta_text: str = ""
    thumbnail_url: str = ""
    media_title: str = ""
    media_type_detected: str = "video"
    estimated_size_text: str = ""
    subtitles_enabled: bool = False
    embed_subtitles: bool = False
    subtitles_langs: str = ""
    convert_subs: str = ""
    cookies_from_browser: str = ""
    cookies_file: str = ""
    proxy: str = ""
    thumbnails_enabled: bool = False
    embed_thumbnail: bool = False
    convert_thumbnails: str = ""
    playlist_start: int | None = None
    playlist_end: int | None = None
    skip_unavailable: bool = False
    no_abort_on_error: bool = False
    rate_limit: str = ""
    sleep_interval: float | None = None
    sleep_requests: float | None = None
    download_archive: str = ""
    format_sort: str = ""
    yt_dlp_version: str = ""
    verbose: bool = False
    no_warnings: bool = False
    geobypass: bool = False
    max_downloads: int | None = None
    playlist_reverse: bool = False
    embed_chapters: bool = False
    split_chapters: bool = False
    write_info_json: bool = False
    write_description: bool = False
    write_annotations: bool = False
    add_metadata: bool = False
    playlist_random: bool = False
    user_agent: str = ""
    referer: str = ""
    socket_timeout: float | None = None
    history: list[HistoryEntry] = field(default_factory=list)

    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def set_history(self, entries: list[HistoryEntry]) -> None:
        with self._lock:
            self.history = entries[:50]

    def append_history(self, entry: HistoryEntry) -> None:
        with self._lock:
            self.history.insert(0, entry)
            # Keep history bounded for long sessions.
            if len(self.history) > 50:
                self.history = self.history[:50]

    def clear_history(self) -> None:
        with self._lock:
            self.history = []

    def set_downloading(self, value: bool) -> None:
        with self._lock:
            self.is_downloading = value

    def reset_progress(self, status_text: str = "Idle") -> None:
        with self._lock:
            self.progress = 0.0
            self.status_text = status_text
            self.speed_text = ""
            self.eta_text = ""
