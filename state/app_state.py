from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Optional


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
    history: list[str] = field(default_factory=list)

    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def append_history(self, entry: str) -> None:
        with self._lock:
            self.history.insert(0, entry)
            # Keep history bounded for long sessions.
            if len(self.history) > 50:
                self.history = self.history[:50]

    def set_downloading(self, value: bool) -> None:
        with self._lock:
            self.is_downloading = value

    def reset_progress(self, status_text: str = "Idle") -> None:
        with self._lock:
            self.progress = 0.0
            self.status_text = status_text
            self.speed_text = ""
            self.eta_text = ""
