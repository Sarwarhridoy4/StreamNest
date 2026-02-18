from __future__ import annotations

from pathlib import Path

import flet as ft

from services.downloader import DownloadRequest, DownloadResult, ProgressInfo
from utils.file_manager import ensure_download_directory, format_eta, format_speed, format_bytes
from utils.validators import is_valid_url


class DownloadMixin:
    def _on_download(self, _: ft.ControlEvent) -> None:
        self.state.url = self.url_field.value.strip() if self.url_field.value else ""

        if not is_valid_url(self.state.url):
            self._set_status("Invalid URL. Please enter a valid link.")
            return

        if self.downloader.is_busy():
            self._set_status("A download is already running.")
            return

        if not self.state.media_title:
            self._set_status("Please click Load Formats first.")
            return

        self.state.set_downloading(True)
        self.active_download_context = "single"
        self.state.status_text = "Starting download..."
        self.state.progress = 0.0
        self.state.speed_text = ""
        self.state.eta_text = ""
        self._reset_ytdlp_logs()
        self._append_ytdlp_log(f"Starting single download: {self.state.url}")

        request = DownloadRequest(
            url=self.state.url,
            mode=self.state.selected_mode,
            quality=self.state.selected_quality,
            save_dir=ensure_download_directory(self.state.save_directory),
        )

        started = self.downloader.start_download(
            request=request,
            on_progress=lambda info: self._run_ui(lambda: self._handle_progress(info)),
            on_done=lambda result: self._run_ui(lambda: self._handle_done(result)),
            on_error=lambda err: self._run_ui(lambda: self._handle_error(err)),
            on_log=lambda text: self._run_ui(lambda text=text: self._append_ytdlp_log(text)),
        )

        if not started:
            self.state.set_downloading(False)
            self._set_status("Unable to start download. Another task is active.")

        self._refresh_view()

    def _on_cancel(self, _: ft.ControlEvent) -> None:
        self.downloader.cancel()
        self._set_status("Canceling download...")

    def _fetch_formats(self) -> None:
        if self.state.is_fetching_formats:
            return

        self.state.is_fetching_formats = True
        self._set_status("Fetching formats...")
        self.page.run_thread(self._fetch_formats_worker, self.state.url)

    def _fetch_formats_worker(self, url: str) -> None:
        try:
            media_info = self.extractor.extract(url)

            def _apply() -> None:
                self.state.media_title = media_info.title
                self.state.thumbnail_url = media_info.thumbnail
                self.state.media_type_detected = "playlist" if media_info.is_playlist else "video"
                self.quality_options = media_info.options
                self._apply_quality_options()
                self._update_estimated_size()
                self._set_status("Formats loaded")
                self._show_popup("Formats loaded successfully.", ft.Colors.GREEN_700)

            self._run_ui(_apply)
        except Exception as exc:  # noqa: BLE001
            self._run_ui(lambda: self._set_status(f"Format extraction failed: {exc}"))
        finally:
            def _finalize() -> None:
                self.state.is_fetching_formats = False
                self._refresh_view()

            self._run_ui(_finalize)

    def _apply_quality_options(self) -> None:
        self.quality_dropdown.options = [
            ft.dropdown.Option(key=opt.value, text=opt.label) for opt in self.quality_options
        ]

        available_values = {opt.value for opt in self.quality_options}
        if self.state.selected_quality not in available_values:
            self.state.selected_quality = "best"
        self.quality_dropdown.value = self.state.selected_quality
        try:
            self.quality_dropdown.update()
        except Exception:
            self._page_update()

    def _update_estimated_size(self) -> None:
        selected = next(
            (opt for opt in self.quality_options if opt.value == self.state.selected_quality),
            None,
        )

        if selected and selected.filesize:
            self.state.estimated_size_text = f"Estimated size: {format_bytes(selected.filesize)}"
        else:
            self.state.estimated_size_text = "Estimated size: Unknown"

    def _handle_progress(self, info: ProgressInfo) -> None:
        if self.active_download_context == "playlist":
            if info.filename:
                self.playlist_current_file = Path(info.filename).name or info.filename
            self.playlist_progress = info.percent
            if info.status == "postprocessing":
                self.playlist_live_status = "Post-processing with FFmpeg..."
            elif info.status == "finished":
                self.playlist_live_status = "Processing downloaded media..."
            else:
                self.playlist_live_status = f"Downloading... {int(info.percent * 100)}%"
            self.playlist_speed = format_speed(info.speed)
            self.playlist_eta = format_eta(info.eta)
        else:
            self.state.progress = info.percent
            if info.status == "postprocessing":
                self.state.status_text = "Post-processing with FFmpeg..."
            elif info.status == "finished":
                self.state.status_text = "Processing downloaded media..."
            else:
                self.state.status_text = f"Downloading... {int(info.percent * 100)}%"
            self.state.speed_text = format_speed(info.speed)
            self.state.eta_text = format_eta(info.eta)

        self._refresh_view()

    def _handle_done(self, result: DownloadResult) -> None:
        self.state.set_downloading(False)
        self._append_ytdlp_log(f"Result: {result.message}")

        if self.active_download_context == "playlist":
            self.playlist_progress = 1.0 if result.success else self.playlist_progress
            self.playlist_speed = ""
            self.playlist_eta = ""
            self.playlist_live_status = result.message
            self.playlist_current_file = "-"
            self._set_playlist_status(result.message)
        else:
            self.state.progress = 1.0 if result.success else self.state.progress
            self.state.speed_text = ""
            self.state.eta_text = ""
            self.state.status_text = result.message

        if result.success:
            self._append_download_history(result)
            self._show_popup("Download completed.", ft.Colors.GREEN_700)
            self._show_result_dialog("Download Completed", result.message)
        else:
            self._show_result_dialog("Download Failed", result.message)

        self._refresh_view()

    def _handle_error(self, err: str) -> None:
        self.state.set_downloading(False)
        self._append_ytdlp_log(f"ERROR: {err}")
        if self.active_download_context == "playlist":
            self.playlist_live_status = f"Error: {err}"
            self.playlist_speed = ""
            self.playlist_eta = ""
            self.playlist_current_file = "-"
            self._set_playlist_status(f"Error: {err}")
        else:
            self.state.status_text = f"Error: {err}"
            self.state.speed_text = ""
            self.state.eta_text = ""
        self._show_result_dialog("Download Error", err)
        self._refresh_view()

