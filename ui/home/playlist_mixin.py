from __future__ import annotations

import flet as ft

from services.downloader import DownloadRequest
from services.format_extractor import FormatExtractor, QualityOption
from utils.file_manager import ensure_download_directory
from utils.validators import is_valid_url


class PlaylistMixin:
    def _on_open_playlist_dialog(self, _: ft.ControlEvent) -> None:
        self.playlist_url_field.value = self.url_field.value or self.state.url
        self.bottom_tab_index = 1
        self.bottom_nav.selected_index = 1
        self._set_active_panel()
        self._page_update()

    def _on_close_playlist_dialog(self, _: ft.ControlEvent) -> None:
        self.bottom_tab_index = 0
        self.bottom_nav.selected_index = 0
        self._set_active_panel()
        self._page_update()

    def _on_load_playlist(self, _: ft.ControlEvent) -> None:
        url = self.playlist_url_field.value.strip() if self.playlist_url_field.value else ""
        range_expr = self.playlist_range_field.value.strip() if self.playlist_range_field.value else ""

        if not is_valid_url(url):
            self._set_playlist_status("Invalid playlist URL.")
            return

        self._set_playlist_status("Loading playlist and formats...")
        self._show_popup("Loading playlist...", ft.Colors.BLUE_700)
        self.page.run_thread(self._load_playlist_worker, url, range_expr)

    def _load_playlist_worker(self, url: str, range_expr: str) -> None:
        try:
            normalized_range = FormatExtractor.normalize_playlist_range(range_expr)
            info = self.extractor.extract_playlist(url, normalized_range or None)

            def _apply() -> None:
                self.playlist_entries = info.entries
                self.playlist_selected_indices = {entry.index for entry in info.entries}
                self.playlist_quality_options = info.options or [
                    QualityOption(label="Best", value="best"),
                    QualityOption(label="Worst", value="worst"),
                ]
                self._apply_playlist_quality_options()
                self._render_playlist_entries()
                self._set_playlist_status(
                    f"Loaded {len(info.entries)} item(s) from '{info.title}'."
                )
                self._show_popup(f"Playlist loaded: {len(info.entries)} item(s).", ft.Colors.GREEN_700)

            self._run_ui(_apply)
        except ValueError as exc:
            error_msg = str(exc)
            self._run_ui(lambda: self._set_playlist_status(error_msg))
        except Exception as exc:  # noqa: BLE001
            error_msg = str(exc)
            self._run_ui(lambda: self._set_playlist_status(f"Playlist load failed: {error_msg}"))

    def _on_playlist_item_toggle(self, event: ft.ControlEvent) -> None:
        raw_index = event.control.data
        if not isinstance(raw_index, int):
            return
        if event.control.value:
            self.playlist_selected_indices.add(raw_index)
        else:
            self.playlist_selected_indices.discard(raw_index)

    def _on_playlist_select_all(self, _: ft.ControlEvent) -> None:
        self.playlist_selected_indices = {entry.index for entry in self.playlist_entries}
        self._render_playlist_entries()
        self._set_playlist_status(f"Selected {len(self.playlist_selected_indices)} item(s).")

    def _on_playlist_clear(self, _: ft.ControlEvent) -> None:
        self.playlist_selected_indices.clear()
        self._render_playlist_entries()
        self._set_playlist_status("Selection cleared.")

    def _on_playlist_download(self, _: ft.ControlEvent) -> None:
        if self.downloader.is_busy():
            self._set_status("A download is already running.")
            self._set_playlist_status("A download is already running.")
            return

        url = self.playlist_url_field.value.strip() if self.playlist_url_field.value else ""
        if not is_valid_url(url):
            self._set_playlist_status("Invalid playlist URL.")
            return

        if not self.playlist_entries:
            self._set_playlist_status("Load playlist first.")
            return

        if not self.playlist_selected_indices:
            self._set_playlist_status("Select at least one playlist item.")
            return

        selected_expr = ",".join(str(i) for i in sorted(self.playlist_selected_indices))

        self.state.set_downloading(True)
        self.active_download_context = "playlist"
        self.state.status_text = "Starting playlist download..."
        self.playlist_progress = 0.0
        self.playlist_speed = ""
        self.playlist_eta = ""
        self.playlist_live_status = "Starting playlist download..."
        self.playlist_current_file = "-"
        self._reset_ytdlp_logs()
        self._append_ytdlp_log(f"Starting playlist download: {url}")
        self._append_ytdlp_log(f"Selected playlist entries: {selected_expr}")

        request = DownloadRequest(
            url=url,
            mode="playlist",
            quality=self.playlist_selected_quality,
            save_dir=ensure_download_directory(self.state.playlist_save_directory),
            playlist_items=selected_expr,
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
            self._set_playlist_status("Unable to start download. Another task is active.")
        else:
            self._set_playlist_status(
                f"Downloading {len(self.playlist_selected_indices)} selected item(s)..."
            )

        self._refresh_view()

    def _apply_playlist_quality_options(self) -> None:
        self.playlist_quality_dropdown.options = [
            ft.dropdown.Option(key=opt.value, text=opt.label) for opt in self.playlist_quality_options
        ]

        available_values = {opt.value for opt in self.playlist_quality_options}
        if self.playlist_selected_quality not in available_values:
            self.playlist_selected_quality = "best"
        self.playlist_quality_dropdown.value = self.playlist_selected_quality
        try:
            self.playlist_quality_dropdown.update()
        except Exception:
            self._page_update()

    def _render_playlist_entries(self) -> None:
        self.playlist_items_list.controls = [
            ft.Checkbox(
                label=f"{entry.index}. {entry.title}",
                value=entry.index in self.playlist_selected_indices,
                data=entry.index,
                on_change=self._on_playlist_item_toggle,
            )
            for entry in self.playlist_entries
        ]
        self._page_update()

    def _set_playlist_status(self, text: str) -> None:
        self.playlist_status_message = text
        self.playlist_status_text.value = text
        self._page_update()
