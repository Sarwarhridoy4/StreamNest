from __future__ import annotations

from datetime import datetime
import os
import platform
import subprocess
from typing import Callable

import flet as ft

from services.downloader import DownloadRequest, DownloadResult, DownloaderService, ProgressInfo
from services.format_extractor import (
    FormatExtractor,
    PlaylistEntry,
    PlaylistInfo,
    QualityOption,
)
from state.app_state import AppState
from ui.components import (
    build_header,
    labeled_control,
    primary_button,
    secondary_button,
    status_chip,
)
from utils.file_manager import ensure_download_directory, format_bytes, format_eta, format_speed
from utils.validators import is_valid_url, is_youtube_url


class HomeView:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        default_dir = ensure_download_directory(None)
        self.state = AppState(save_directory=default_dir, playlist_save_directory=default_dir)

        self.downloader = DownloaderService()
        self.extractor = FormatExtractor()

        self.quality_options: list[QualityOption] = [
            QualityOption(label="Best", value="best"),
            QualityOption(label="Worst", value="worst"),
        ]

        self.playlist_quality_options: list[QualityOption] = [
            QualityOption(label="Best", value="best"),
            QualityOption(label="Worst", value="worst"),
        ]
        self.playlist_selected_quality = "best"
        self.playlist_entries: list[PlaylistEntry] = []
        self.playlist_selected_indices: set[int] = set()
        self.playlist_status_message = "Load playlist to choose items."
        self.active_download_context = "single"
        self.playlist_progress = 0.0
        self.playlist_speed = ""
        self.playlist_eta = ""
        self.playlist_live_status = "Idle"

        self._build_controls()
        self._apply_quality_options()
        self._apply_playlist_quality_options()
        self._refresh_view()

    def _build_controls(self) -> None:
        self.url_field = ft.TextField(
            label="YouTube URL",
            hint_text="Paste video URL",
            on_submit=self._on_url_commit,
            on_blur=self._on_url_commit,
            expand=True,
        )

        self.load_formats_btn = secondary_button("Load Formats", self._on_load_formats)
        self.open_playlist_btn = secondary_button("Open Playlist Window", self._on_open_playlist_dialog)

        self.quality_dropdown = ft.Dropdown(
            label="Quality",
            value="best",
            options=[],
            on_select=self._on_quality_change,
            expand=True,
        )

        self.mode_group = ft.RadioGroup(
            value="video",
            on_change=self._on_mode_change,
            content=ft.Row(
                controls=[
                    ft.Radio(value="video", label="Video (MP4)"),
                    ft.Radio(value="audio", label="Audio (MP3)"),
                ],
                wrap=True,
                spacing=12,
            ),
        )

        self.directory_picker = ft.FilePicker()
        self.page.services.append(self.directory_picker)

        self.save_dir_text = ft.Text(self.state.save_directory, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)
        self.pick_dir_btn = secondary_button("Choose Save Folder", self._on_pick_directory)
        self.open_dir_btn = secondary_button("Open Folder", self._on_open_directory)

        self.progress_bar = ft.ProgressBar(value=0.0)
        self.status_text = ft.Text("Idle")
        self.speed_text = ft.Text("", selectable=False)
        self.eta_text = ft.Text("", selectable=False)
        self.size_text = ft.Text("", selectable=False)

        self.download_btn = primary_button("Download", self._on_download)
        self.cancel_btn = secondary_button("Cancel", self._on_cancel, disabled=True)

        self.theme_switch = ft.Switch(label="Dark theme", value=False, on_change=self._on_theme_toggle)

        self.thumbnail = ft.Image(
            src="",
            fit=ft.BoxFit.COVER,
            border_radius=12,
            visible=False,
            expand=True,
        )
        self.title_text = ft.Text("", weight=ft.FontWeight.W_500, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)

        self.history_list = ft.ListView(spacing=6, auto_scroll=False, expand=True)

        # Playlist dialog controls
        self.playlist_url_field = ft.TextField(label="Playlist URL", hint_text="Paste YouTube playlist URL")
        self.playlist_range_field = ft.TextField(
            label="Range",
            hint_text="Examples: 1-5 or 1,3,7-10 (leave empty for all)",
        )

        self.playlist_quality_dropdown = ft.Dropdown(
            label="Quality",
            value="best",
            options=[],
            on_select=self._on_playlist_quality_change,
        )

        self.playlist_save_dir_text = ft.Text(
            self.state.playlist_save_directory,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.playlist_pick_dir_btn = secondary_button("Choose Save Folder", self._on_pick_playlist_directory)
        self.playlist_open_dir_btn = secondary_button("Open Folder", self._on_open_playlist_directory)

        self.playlist_status_text = ft.Text(self.playlist_status_message)
        self.playlist_progress_bar = ft.ProgressBar(value=0.0)
        self.playlist_live_status_text = ft.Text(self.playlist_live_status)
        self.playlist_speed_text = ft.Text("-", selectable=False)
        self.playlist_eta_text = ft.Text("-", selectable=False)
        self.playlist_items_list = ft.ListView(spacing=4, auto_scroll=True, height=220)

        self.playlist_load_btn = primary_button("Load Playlist", self._on_load_playlist)
        self.playlist_download_btn = primary_button("Download Selected", self._on_playlist_download)
        self.playlist_select_all_btn = ft.TextButton(content="Select all", on_click=self._on_playlist_select_all)
        self.playlist_clear_btn = ft.TextButton(content="Clear", on_click=self._on_playlist_clear)

        self.playlist_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Playlist Downloader"),
            content=ft.Container(
                width=720,
                content=ft.Column(
                    controls=[
                        self.playlist_url_field,
                        self.playlist_range_field,
                        ft.ResponsiveRow(
                            controls=[
                                ft.Container(col={"xs": 12, "sm": 6}, content=self.playlist_load_btn),
                                ft.Container(col={"xs": 12, "sm": 6}, content=self.playlist_download_btn),
                            ],
                            spacing=8,
                            run_spacing=8,
                        ),
                        ft.ResponsiveRow(
                            controls=[
                                ft.Container(col={"xs": 12, "sm": 6}, content=self.playlist_quality_dropdown),
                                ft.Container(
                                    col={"xs": 12, "sm": 6},
                                    content=ft.Column(
                                        controls=[
                                            self.playlist_pick_dir_btn,
                                            self.playlist_open_dir_btn,
                                            self.playlist_save_dir_text,
                                        ],
                                        spacing=8,
                                    ),
                                ),
                            ],
                            spacing=8,
                            run_spacing=8,
                        ),
                        self.playlist_progress_bar,
                        self.playlist_live_status_text,
                        ft.ResponsiveRow(
                            controls=[
                                ft.Container(col={"xs": 12, "sm": 6}, content=status_chip("Speed", self.playlist_speed_text)),
                                ft.Container(col={"xs": 12, "sm": 6}, content=status_chip("ETA", self.playlist_eta_text)),
                            ],
                            spacing=8,
                            run_spacing=8,
                        ),
                        ft.Row(controls=[self.playlist_select_all_btn, self.playlist_clear_btn], spacing=6),
                        ft.Text("Playlist Items", weight=ft.FontWeight.W_500),
                        self.playlist_items_list,
                        self.playlist_status_text,
                    ],
                    spacing=10,
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
            actions=[ft.TextButton(content="Close", on_click=self._on_close_playlist_dialog)],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def build(self) -> ft.Control:
        header = build_header(
            "StreamNest Downloader",
            "Load formats dynamically, then download video/audio or selected playlist items.",
        )

        left_panel = ft.Container(
            padding=16,
            bgcolor=ft.Colors.SURFACE,
            border_radius=12,
            expand=True,
            content=ft.Column(
                controls=[
                    header,
                    labeled_control("URL", self.url_field),
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(col={"xs": 12, "sm": 6}, content=self.load_formats_btn),
                            ft.Container(col={"xs": 12, "sm": 6}, content=self.open_playlist_btn),
                        ],
                        spacing=8,
                        run_spacing=8,
                    ),
                    labeled_control("Mode", self.mode_group),
                    ft.ResponsiveRow(
                        controls=[
                            labeled_control("Quality", self.quality_dropdown),
                            labeled_control(
                                "Save Location",
                                ft.Column(
                                    controls=[self.pick_dir_btn, self.open_dir_btn, self.save_dir_text],
                                    spacing=8,
                                ),
                            ),
                        ],
                    ),
                    self.size_text,
                    self.progress_bar,
                    self.status_text,
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(col={"xs": 12, "sm": 6}, content=status_chip("Speed", self.speed_text)),
                            ft.Container(col={"xs": 12, "sm": 6}, content=status_chip("ETA", self.eta_text)),
                        ],
                        spacing=8,
                        run_spacing=8,
                    ),
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(col={"xs": 12, "sm": 6}, content=self.download_btn),
                            ft.Container(col={"xs": 12, "sm": 6}, content=self.cancel_btn),
                        ],
                        spacing=8,
                        run_spacing=8,
                    ),
                    self.theme_switch,
                ],
                spacing=14,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
        )

        right_panel = ft.Container(
            padding=16,
            border_radius=12,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            expand=True,
            content=ft.Column(
                controls=[
                    ft.Text("Preview", theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
                    ft.Container(
                        content=self.thumbnail,
                        height=180,
                        border_radius=12,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    ),
                    self.title_text,
                    ft.Divider(),
                    ft.Container(
                        expand=True,
                        content=ft.Column(
                            controls=[
                                ft.Text("History", theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
                                self.history_list,
                            ],
                            spacing=8,
                            expand=True,
                        ),
                    ),
                ],
                spacing=10,
                expand=True,
            ),
        )

        return ft.SafeArea(
            expand=True,
            content=ft.Container(
                expand=True,
                padding=12,
                content=ft.Column(
                    controls=[left_panel, right_panel],
                    spacing=10,
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
        )

    def _on_url_commit(self, _: ft.ControlEvent) -> None:
        self.state.url = self.url_field.value.strip() if self.url_field.value else ""

    def _on_load_formats(self, _: ft.ControlEvent) -> None:
        try:
            self.state.url = self.url_field.value.strip() if self.url_field.value else ""
            if not is_valid_url(self.state.url):
                self._set_status("Invalid URL. Please enter a valid link.")
                return
            if not is_youtube_url(self.state.url):
                self._set_status("Only YouTube URLs are supported.")
                return
            self._show_popup("Loading formats...", ft.Colors.BLUE_700)
            self._fetch_formats()
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Load formats failed: {exc}")

    def _on_mode_change(self, _: ft.ControlEvent) -> None:
        self.state.selected_mode = self.mode_group.value or "video"
        self._refresh_view()

    def _on_quality_change(self, _: ft.ControlEvent) -> None:
        self.state.selected_quality = self.quality_dropdown.value or "best"
        self._update_estimated_size()
        self._refresh_view()

    def _on_playlist_quality_change(self, _: ft.ControlEvent) -> None:
        self.playlist_selected_quality = self.playlist_quality_dropdown.value or "best"
        self._page_update()

    async def _on_pick_directory(self, _: ft.ControlEvent) -> None:
        await self._pick_directory(for_playlist=False)

    async def _on_pick_playlist_directory(self, _: ft.ControlEvent) -> None:
        await self._pick_directory(for_playlist=True)

    def _on_open_directory(self, _: ft.ControlEvent) -> None:
        self._open_folder(self.state.save_directory, for_playlist=False)

    def _on_open_playlist_directory(self, _: ft.ControlEvent) -> None:
        self._open_folder(self.state.playlist_save_directory, for_playlist=True)

    def _open_folder(self, path: str, for_playlist: bool) -> None:
        folder = ensure_download_directory(path)

        def _worker() -> None:
            try:
                system = platform.system().lower()
                if system.startswith("windows"):
                    os.startfile(folder)  # type: ignore[attr-defined]
                elif system == "darwin":
                    subprocess.Popen(["open", folder])  # noqa: S603,S607
                else:
                    subprocess.Popen(["xdg-open", folder])  # noqa: S603,S607
            except Exception as exc:  # noqa: BLE001
                if for_playlist:
                    self._run_ui(lambda: self._set_playlist_status(f"Open folder failed: {exc}"))
                else:
                    self._run_ui(lambda: self._set_status(f"Open folder failed: {exc}"))

        self.page.run_thread(_worker)

    async def _pick_directory(self, for_playlist: bool) -> None:
        current = self.state.playlist_save_directory if for_playlist else self.state.save_directory
        try:
            selected_path = await self.directory_picker.get_directory_path(
                dialog_title="Select download location",
                initial_directory=current,
            )
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Directory picker error: {exc}")
            return

        if selected_path:
            normalized = ensure_download_directory(selected_path)
            if for_playlist:
                self.state.playlist_save_directory = normalized
                self.playlist_save_dir_text.value = normalized
                self._set_playlist_status("Playlist save folder updated.")
                self._page_update()
            else:
                self.state.save_directory = normalized
                self._refresh_view()

    def _on_download(self, _: ft.ControlEvent) -> None:
        self.state.url = self.url_field.value.strip() if self.url_field.value else ""

        if not is_valid_url(self.state.url):
            self._set_status("Invalid URL. Please enter a valid link.")
            return

        if not is_youtube_url(self.state.url):
            self._set_status("Only YouTube URLs are supported.")
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
        )

        if not started:
            self.state.set_downloading(False)
            self._set_status("Unable to start download. Another task is active.")

        self._refresh_view()

    def _on_cancel(self, _: ft.ControlEvent) -> None:
        self.downloader.cancel()
        self._set_status("Canceling download...")

    def _on_theme_toggle(self, _: ft.ControlEvent) -> None:
        self.page.theme_mode = ft.ThemeMode.DARK if self.theme_switch.value else ft.ThemeMode.LIGHT
        self._page_update()

    def _on_open_playlist_dialog(self, _: ft.ControlEvent) -> None:
        try:
            self.playlist_url_field.value = self.url_field.value or self.state.url
            self.page.show_dialog(self.playlist_dialog)
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Open playlist window failed: {exc}")

    def _on_close_playlist_dialog(self, _: ft.ControlEvent) -> None:
        try:
            self.page.pop_dialog()
        except Exception:  # noqa: BLE001
            self.playlist_dialog.open = False
            self._page_update()

    def _on_load_playlist(self, _: ft.ControlEvent) -> None:
        url = self.playlist_url_field.value.strip() if self.playlist_url_field.value else ""
        range_expr = self.playlist_range_field.value.strip() if self.playlist_range_field.value else ""

        if not is_valid_url(url):
            self._set_playlist_status("Invalid playlist URL.")
            return

        if not is_youtube_url(url):
            self._set_playlist_status("Only YouTube URLs are supported.")
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
            self._run_ui(lambda: self._set_playlist_status(str(exc)))
        except Exception as exc:  # noqa: BLE001
            self._run_ui(lambda: self._set_playlist_status(f"Playlist load failed: {exc}"))

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
        if not is_valid_url(url) or not is_youtube_url(url):
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
        )

        if not started:
            self.state.set_downloading(False)
            self._set_playlist_status("Unable to start download. Another task is active.")
        else:
            self._set_playlist_status(
                f"Downloading {len(self.playlist_selected_indices)} selected item(s)..."
            )

        self._refresh_view()

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

        if self.active_download_context == "playlist":
            self.playlist_progress = 1.0 if result.success else self.playlist_progress
            self.playlist_speed = ""
            self.playlist_eta = ""
            self.playlist_live_status = result.message
            self._set_playlist_status(result.message)
        else:
            self.state.progress = 1.0 if result.success else self.state.progress
            self.state.speed_text = ""
            self.state.eta_text = ""
            self.state.status_text = result.message

        if result.success:
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.state.append_history(f"{stamp} - {self.state.media_title or self.state.url or 'Playlist download'}")
            self._render_history()
            self._show_popup("Download completed.", ft.Colors.GREEN_700)

        self._refresh_view()

    def _handle_error(self, err: str) -> None:
        self.state.set_downloading(False)
        if self.active_download_context == "playlist":
            self.playlist_live_status = f"Error: {err}"
            self.playlist_speed = ""
            self.playlist_eta = ""
            self._set_playlist_status(f"Error: {err}")
        else:
            self.state.status_text = f"Error: {err}"
            self.state.speed_text = ""
            self.state.eta_text = ""
        self._refresh_view()

    def _render_history(self) -> None:
        self.history_list.controls = [
            ft.Container(
                content=ft.Text(item, size=12),
                padding=8,
                border_radius=8,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            )
            for item in self.state.history
        ]

    def _set_status(self, text: str) -> None:
        self.state.status_text = text
        self._refresh_view()

    def _set_playlist_status(self, text: str) -> None:
        self.playlist_status_message = text
        self.playlist_status_text.value = text
        self._page_update()

    def _show_popup(self, message: str, color: ft.Colors | str = ft.Colors.BLUE_GREY_700) -> None:
        try:
            self.page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(message),
                    bgcolor=color,
                    duration=1800,
                )
            )
        except Exception:
            self.state.status_text = message
            self._page_update()

    def _refresh_view(self) -> None:
        self.url_field.value = self.state.url
        self.save_dir_text.value = self.state.save_directory
        self.status_text.value = self.state.status_text
        self.progress_bar.value = self.state.progress
        self.speed_text.value = self.state.speed_text or "-"
        self.eta_text.value = self.state.eta_text or "-"
        self.size_text.value = self.state.estimated_size_text

        self.download_btn.disabled = self.state.is_downloading
        self.cancel_btn.disabled = not self.state.is_downloading

        self.mode_group.value = self.state.selected_mode
        self.quality_dropdown.value = self.state.selected_quality

        self.title_text.value = self.state.media_title or ""
        self.thumbnail.src = self.state.thumbnail_url
        self.thumbnail.visible = bool(self.state.thumbnail_url)

        self.playlist_save_dir_text.value = self.state.playlist_save_directory
        self.playlist_status_text.value = self.playlist_status_message
        self.playlist_progress_bar.value = self.playlist_progress
        self.playlist_live_status_text.value = self.playlist_live_status
        self.playlist_speed_text.value = self.playlist_speed or "-"
        self.playlist_eta_text.value = self.playlist_eta or "-"

        self._render_history()
        self._page_update()

    def _run_ui(self, action: Callable[[], None]) -> None:
        async def _apply() -> None:
            action()

        self.page.run_task(_apply)

    def _page_update(self) -> None:
        self.page.update()
