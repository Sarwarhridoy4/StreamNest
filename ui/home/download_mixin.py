from __future__ import annotations

from pathlib import Path

import flet as ft

from services.downloader import DownloadRequest, DownloadResult, ProgressInfo
from utils.file_manager import ensure_download_directory, format_bytes, format_eta, format_speed
from utils.validators import is_valid_url


class DownloadMixin:
    def _set_download_controls_loading(self, is_loading: bool) -> None:
        """Toggle download/cancel button states during an active download."""
        self.download_btn.disabled = is_loading
        self.cancel_btn.disabled = not is_loading
        if is_loading:
            self.download_btn.text = "Downloading\u2026"
        else:
            self.download_btn.text = "Download"
        try:
            self.download_btn.update()
            self.cancel_btn.update()
        except Exception:
            self._page_update()

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
        self._set_download_controls_loading(is_loading=True)

        request = DownloadRequest(
            url=self.state.url,
            mode=self.state.selected_mode,
            quality=self.state.selected_quality,
            save_dir=ensure_download_directory(self.state.save_directory),
            subtitles=self.state.subtitles_enabled,
            embed_subtitles=self.state.embed_subtitles,
            subtitles_langs=self.state.subtitles_langs or None,
            convert_subs=self.state.convert_subs or None,
            cookies_from_browser=self.state.cookies_from_browser or None,
            cookies_file=self.state.cookies_file or None,
            proxy=self.state.proxy or None,
            thumbnails=self.state.thumbnails_enabled,
            embed_thumbnail=self.state.embed_thumbnail,
            convert_thumbnails=self.state.convert_thumbnails or None,
            rate_limit=self.state.rate_limit or None,
            sleep_interval=self.state.sleep_interval,
            sleep_requests=self.state.sleep_requests,
            download_archive=self.state.download_archive or None,
            format_sort=self.state.format_sort or None,
            verbose=self.state.verbose,
            no_warnings=self.state.no_warnings,
            geobypass=self.state.geobypass,
            max_downloads=self.state.max_downloads,
            playlist_reverse=self.state.playlist_reverse,
            embed_chapters=self.state.embed_chapters,
            split_chapters=self.state.split_chapters,
            write_info_json=self.state.write_info_json,
            write_description=self.state.write_description,
            write_annotations=self.state.write_annotations,
            add_metadata=self.state.add_metadata,
            playlist_random=self.state.playlist_random,
            user_agent=self.state.user_agent or None,
            referer=self.state.referer or None,
            socket_timeout=self.state.socket_timeout,
            no_overwrites=self.state.no_overwrites,
            force_overwrites=self.state.force_overwrites,
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
            self._set_download_controls_loading(is_loading=False)
            self._set_status("Unable to start download. Another task is active.")

        self._refresh_view()

    def _on_cancel(self, _: ft.ControlEvent) -> None:
        self.downloader.cancel()
        self._set_download_controls_loading(is_loading=False)
        self._set_status("Canceling download...")

    def _on_subtitles_change(self, _: ft.ControlEvent) -> None:
        self.state.subtitles_enabled = bool(self.subtitles_checkbox.value)
        self.state.embed_subtitles = bool(self.embed_subtitles_checkbox.value)
        self.state.subtitles_langs = (self.subtitles_langs_field.value or "").strip()
        self.state.convert_subs = self.convert_subs_dropdown.value or ""
        self._refresh_view()

    def _on_cookies_proxy_change(self, _: ft.ControlEvent) -> None:
        self.state.cookies_from_browser = self.cookies_browser_dropdown.value or ""
        self.state.cookies_file = (self.cookies_file_field.value or "").strip()
        self.state.proxy = (self.proxy_field.value or "").strip()
        self._refresh_view()

    def _on_thumbnails_change(self, _: ft.ControlEvent) -> None:
        self.state.thumbnails_enabled = bool(self.thumbnails_checkbox.value)
        self.state.embed_thumbnail = bool(self.embed_thumbnail_checkbox.value)
        self.state.convert_thumbnails = self.convert_thumbnails_dropdown.value or ""
        self._refresh_view()

    def _on_playlist_options_change(self, _: ft.ControlEvent) -> None:
        start = self._parse_positive_int(self.playlist_start_field.value)
        end = self._parse_positive_int(self.playlist_end_field.value)
        self.state.playlist_start = start
        self.state.playlist_end = end
        self.state.skip_unavailable = bool(self.skip_unavailable_checkbox.value)
        self.state.no_abort_on_error = bool(self.no_abort_on_error_checkbox.value)
        self._refresh_view()

    def _on_rate_limit_sleep_change(self, _: ft.ControlEvent) -> None:
        self.state.rate_limit = (self.rate_limit_field.value or "").strip()
        self.state.sleep_interval = self._parse_optional_float(self.sleep_interval_field.value)
        self.state.sleep_requests = self._parse_optional_float(self.sleep_requests_field.value)
        self._refresh_view()

    def _on_archive_change(self, _: ft.ControlEvent) -> None:
        self.state.download_archive = (self.download_archive_field.value or "").strip()
        self._refresh_view()

    def _on_format_sort_change(self, _: ft.ControlEvent) -> None:
        self.state.format_sort = (self.format_sort_field.value or "").strip()
        self._refresh_view()

    def _on_verbose_change(self, _: ft.ControlEvent) -> None:
        self.state.verbose = bool(self.verbose_checkbox.value)
        self._refresh_view()

    def _on_no_warnings_change(self, _: ft.ControlEvent) -> None:
        self.state.no_warnings = bool(self.no_warnings_checkbox.value)
        self._refresh_view()

    def _on_geo_bypass_change(self, _: ft.ControlEvent) -> None:
        self.state.geobypass = bool(self.geobypass_checkbox.value)
        self._refresh_view()

    def _on_max_downloads_change(self, _: ft.ControlEvent) -> None:
        self.state.max_downloads = self._parse_positive_int(self.max_downloads_field.value)
        self._refresh_view()

    def _on_playlist_reverse_change(self, _: ft.ControlEvent) -> None:
        self.state.playlist_reverse = bool(self.playlist_reverse_checkbox.value)
        self._refresh_view()

    def _on_embed_chapters_change(self, _: ft.ControlEvent) -> None:
        self.state.embed_chapters = bool(self.embed_chapters_checkbox.value)
        self._refresh_view()

    def _on_split_chapters_change(self, _: ft.ControlEvent) -> None:
        self.state.split_chapters = bool(self.split_chapters_checkbox.value)
        self._refresh_view()

    def _on_write_info_json_change(self, _: ft.ControlEvent) -> None:
        self.state.write_info_json = bool(self.write_info_json_checkbox.value)
        self._refresh_view()

    def _on_write_description_change(self, _: ft.ControlEvent) -> None:
        self.state.write_description = bool(self.write_description_checkbox.value)
        self._refresh_view()

    def _on_write_annotations_change(self, _: ft.ControlEvent) -> None:
        self.state.write_annotations = bool(self.write_annotations_checkbox.value)
        self._refresh_view()

    def _on_add_metadata_change(self, _: ft.ControlEvent) -> None:
        self.state.add_metadata = bool(self.add_metadata_checkbox.value)
        self._refresh_view()

    def _on_playlist_random_change(self, _: ft.ControlEvent) -> None:
        self.state.playlist_random = bool(self.playlist_random_checkbox.value)
        self._refresh_view()

    def _on_user_agent_referer_change(self, _: ft.ControlEvent) -> None:
        self.state.user_agent = (self.user_agent_field.value or "").strip()
        self.state.referer = (self.referer_field.value or "").strip()
        self._refresh_view()

    def _on_socket_timeout_change(self, _: ft.ControlEvent) -> None:
        self.state.socket_timeout = self._parse_optional_float(self.socket_timeout_field.value)
        self._refresh_view()

    def _on_no_overwrites_change(self, _: ft.ControlEvent) -> None:
        self.state.no_overwrites = bool(self.no_overwrites_checkbox.value)
        self._refresh_view()

    def _on_force_overwrites_change(self, _: ft.ControlEvent) -> None:
        self.state.force_overwrites = bool(self.force_overwrites_checkbox.value)
        self._refresh_view()

    def _on_update_yt_dlp(self, _: ft.ControlEvent) -> None:
        success, message = self.downloader.update_yt_dlp()
        self.state.yt_dlp_version = self.downloader.get_yt_dlp_version() or ""
        self._set_status("yt-dlp updated successfully." if success else message)
        self._refresh_view()

    @staticmethod
    def _parse_optional_float(value: str | None) -> float | None:
        if not value or not value.strip():
            return None
        try:
            return float(value.strip())
        except ValueError:
            return None

    @staticmethod
    def _parse_positive_int(value: str | None) -> int | None:
        if not value or not value.strip():
            return None
        try:
            num = int(value.strip())
        except ValueError:
            return None
        return num if num > 0 else None

    def _fetch_formats(self) -> None:
        if self.state.is_fetching_formats:
            return

        self.state.is_fetching_formats = True
        self._set_status("Fetching formats...")
        self.load_formats_btn.disabled = True
        try:
            self.load_formats_btn.update()
        except Exception:
            self._page_update()
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
        except Exception as exc:
            error_msg = str(exc)
            self._run_ui(lambda: self._set_status(f"Format extraction failed: {error_msg}"))
        finally:
            def _finalize() -> None:
                self.state.is_fetching_formats = False
                self.load_formats_btn.disabled = False
                try:
                    self.load_formats_btn.update()
                except Exception:
                    self._page_update()
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
        self._set_download_controls_loading(is_loading=False)
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
        self._set_download_controls_loading(is_loading=False)
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

