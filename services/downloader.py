from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
from threading import Event, Lock, Thread
import time
from typing import Any, Callable, Optional

import yt_dlp

from services.format_extractor import FormatExtractor


class DownloadCancelledError(Exception):
    pass


@dataclass
class DownloadRequest:
    url: str
    mode: str  # video | playlist | audio
    quality: str
    save_dir: str
    playlist_items: str | None = None


@dataclass
class ProgressInfo:
    status: str
    percent: float
    downloaded_bytes: int | None = None
    total_bytes: int | None = None
    speed: float | None = None
    eta: int | None = None
    filename: str | None = None


@dataclass
class DownloadResult:
    success: bool
    message: str
    output_path: str | None = None


ProgressCallback = Callable[[ProgressInfo], None]
ResultCallback = Callable[[DownloadResult], None]
ErrorCallback = Callable[[str], None]


class DownloaderService:
    """Threaded yt-dlp wrapper with progress and cancel support."""

    def __init__(self) -> None:
        self._cancel_event = Event()
        self._active_lock = Lock()
        self._active_thread: Optional[Thread] = None
        self._ffmpeg_dir = self._detect_ffmpeg_dir()

    def is_busy(self) -> bool:
        with self._active_lock:
            return self._active_thread is not None and self._active_thread.is_alive()

    def cancel(self) -> None:
        self._cancel_event.set()

    def start_download(
        self,
        request: DownloadRequest,
        on_progress: ProgressCallback,
        on_done: ResultCallback,
        on_error: ErrorCallback,
    ) -> bool:
        with self._active_lock:
            if self._active_thread is not None and self._active_thread.is_alive():
                return False

            self._cancel_event.clear()
            thread = Thread(
                target=self._download_worker,
                args=(request, on_progress, on_done, on_error),
                daemon=True,
            )
            self._active_thread = thread
            thread.start()
            return True

    def _download_worker(
        self,
        request: DownloadRequest,
        on_progress: ProgressCallback,
        on_done: ResultCallback,
        on_error: ErrorCallback,
    ) -> None:
        try:
            ydl_opts = self._build_options(request, on_progress)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([request.url])

            if self._cancel_event.is_set():
                on_done(DownloadResult(success=False, message="Download canceled"))
            else:
                on_done(DownloadResult(success=True, message="Download completed"))
        except DownloadCancelledError:
            on_done(DownloadResult(success=False, message="Download canceled"))
        except yt_dlp.utils.DownloadError as exc:
            on_error(str(exc))
        except Exception as exc:  # noqa: BLE001
            on_error(f"Unexpected error: {exc}")
        finally:
            with self._active_lock:
                self._active_thread = None

    def _build_options(
        self,
        request: DownloadRequest,
        on_progress: ProgressCallback,
    ) -> dict[str, Any]:
        out_template = str(Path(request.save_dir) / "%(title).160s.%(ext)s")

        opts: dict[str, Any] = {
            "outtmpl": out_template,
            "noplaylist": request.mode != "playlist",
            "ignoreerrors": False,
            "retries": 5,
            "continuedl": True,
            "quiet": True,
            "postprocessor_hooks": [self._postprocessor_hook_factory(on_progress)],
            "progress_hooks": [self._progress_hook_factory(on_progress)],
        }

        if self._ffmpeg_dir:
            opts["ffmpeg_location"] = self._ffmpeg_dir

        if request.mode == "playlist" and request.playlist_items:
            opts["playlist_items"] = request.playlist_items

        if request.mode == "audio":
            opts.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ],
                }
            )
        else:
            opts.update(
                {
                    "format": FormatExtractor.resolve_format_selector(
                        request.quality, request.mode
                    ),
                    "merge_output_format": "mp4",
                    "postprocessors": [
                        {
                            "key": "FFmpegVideoRemuxer",
                            "preferedformat": "mp4",
                        },
                        {"key": "FFmpegMetadata"},
                    ],
                }
            )

        return opts

    def _progress_hook_factory(self, on_progress: ProgressCallback) -> Callable[[dict[str, Any]], None]:
        last_downloaded = 0.0
        last_ts = time.monotonic()

        def _hook(data: dict[str, Any]) -> None:
            nonlocal last_downloaded, last_ts
            if self._cancel_event.is_set():
                raise DownloadCancelledError()

            status = data.get("status", "")

            if status == "downloading":
                downloaded = data.get("downloaded_bytes")
                total = data.get("total_bytes") or data.get("total_bytes_estimate")
                speed = data.get("speed")
                eta = data.get("eta")
                percent_hint = data.get("_percent_str")

                percent = 0.0
                if isinstance(downloaded, (int, float)) and isinstance(total, (int, float)) and total > 0:
                    percent = min(max(float(downloaded) / float(total), 0.0), 1.0)
                elif isinstance(percent_hint, str):
                    parsed_percent = self._parse_percent_str(percent_hint)
                    if parsed_percent is not None:
                        percent = parsed_percent

                speed_value = float(speed) if isinstance(speed, (int, float)) else None
                if speed_value is None and isinstance(data.get("_speed_str"), str):
                    speed_value = self._parse_speed_str(data.get("_speed_str"))

                if speed_value is None and isinstance(downloaded, (int, float)):
                    now = time.monotonic()
                    delta_bytes = float(downloaded) - last_downloaded
                    delta_time = now - last_ts
                    if delta_time > 0 and delta_bytes > 0:
                        speed_value = delta_bytes / delta_time
                    last_downloaded = float(downloaded)
                    last_ts = now

                eta_value = int(eta) if isinstance(eta, (int, float)) else None
                if eta_value is None and isinstance(data.get("_eta_str"), str):
                    eta_value = self._parse_eta_str(data.get("_eta_str"))
                if eta_value is None and speed_value and isinstance(total, (int, float)) and isinstance(downloaded, (int, float)):
                    remaining = float(total) - float(downloaded)
                    if remaining > 0:
                        eta_value = int(remaining / speed_value)

                on_progress(
                    ProgressInfo(
                        status="downloading",
                        percent=percent,
                        downloaded_bytes=int(downloaded) if isinstance(downloaded, (int, float)) else None,
                        total_bytes=int(total) if isinstance(total, (int, float)) else None,
                        speed=speed_value,
                        eta=eta_value,
                        filename=data.get("filename"),
                    )
                )
            elif status == "finished":
                on_progress(
                    ProgressInfo(
                        status="finished",
                        percent=1.0,
                        filename=data.get("filename"),
                    )
                )

        return _hook

    @staticmethod
    def _detect_ffmpeg_dir() -> str | None:
        ffmpeg_bin = shutil.which("ffmpeg")
        if not ffmpeg_bin:
            return None
        return str(Path(ffmpeg_bin).resolve().parent)

    def _postprocessor_hook_factory(self, on_progress: ProgressCallback) -> Callable[[dict[str, Any]], None]:
        def _hook(data: dict[str, Any]) -> None:
            if self._cancel_event.is_set():
                raise DownloadCancelledError()

            if data.get("status") in {"started", "processing"}:
                on_progress(
                    ProgressInfo(
                        status="postprocessing",
                        percent=1.0,
                    )
                )

        return _hook

    @staticmethod
    def _parse_percent_str(value: str) -> float | None:
        match = re.search(r"([0-9]+(?:\\.[0-9]+)?)\\s*%", value)
        if not match:
            return None
        return min(max(float(match.group(1)) / 100.0, 0.0), 1.0)

    @staticmethod
    def _parse_eta_str(value: str) -> int | None:
        cleaned = value.strip()
        if not cleaned or cleaned == "N/A":
            return None
        parts = cleaned.split(":")
        if not all(p.isdigit() for p in parts):
            return None
        nums = [int(p) for p in parts]
        if len(nums) == 3:
            return nums[0] * 3600 + nums[1] * 60 + nums[2]
        if len(nums) == 2:
            return nums[0] * 60 + nums[1]
        if len(nums) == 1:
            return nums[0]
        return None

    @staticmethod
    def _parse_speed_str(value: str) -> float | None:
        cleaned = value.strip().replace("iB", "B")
        match = re.search(r"([0-9]+(?:\\.[0-9]+)?)\\s*([KMGTP]?B)/s", cleaned, re.IGNORECASE)
        if not match:
            return None
        magnitude = float(match.group(1))
        unit = match.group(2).upper()
        multipliers = {
            "B": 1.0,
            "KB": 1024.0,
            "MB": 1024.0**2,
            "GB": 1024.0**3,
            "TB": 1024.0**4,
            "PB": 1024.0**5,
        }
        factor = multipliers.get(unit)
        if factor is None:
            return None
        return magnitude * factor
