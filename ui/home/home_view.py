from __future__ import annotations

import os
from pathlib import Path
import platform
import shutil
import subprocess
from typing import Callable

import flet as ft

from services.downloader import DownloaderService
from services.format_extractor import (
    FormatExtractor,
    PlaylistEntry,
    QualityOption,
)
from state.app_state import AppState
from ui.components import YT_RED
from utils.file_manager import ensure_download_directory, resolve_download_directory
from utils.history_store import HistoryStore
from utils.validators import is_valid_url
from ui.home.download_mixin import DownloadMixin
from ui.home.ffmpeg_install_mixin import FfmpegInstallMixin
from ui.home.history_mixin import HistoryMixin
from ui.home.playlist_mixin import PlaylistMixin
from ui.home.control_layout_mixin import ControlLayoutMixin
from ui.home.view_layout_mixin import ViewLayoutMixin


class HomeView(
    FfmpegInstallMixin,
    DownloadMixin,
    PlaylistMixin,
    HistoryMixin,
    ControlLayoutMixin,
    ViewLayoutMixin,
):
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        default_dir = ensure_download_directory(None)
        self.state = AppState(save_directory=default_dir, playlist_save_directory=default_dir)
        self.history_store = HistoryStore()
        self.state.set_history(self.history_store.load())

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
        self.playlist_current_file = "-"
        self.bottom_tab_index = 0
        self.show_welcome = True
        self.platform_name = self._platform_name()
        self.is_mobile_platform = self._is_mobile_platform()
        self.is_android_platform = self._is_android_platform()
        self._platform_theme_listener_enabled = False
        self.ffmpeg_notice_shown = False
        self.ffmpeg_missing = self._is_ffmpeg_missing()
        self.ffmpeg_install_hint = self._build_ffmpeg_install_hint()
        self.ffmpeg_install_supported = self._supports_ffmpeg_auto_install()
        self.ffmpeg_install_running = False
        self.pending_ffmpeg_install_plan: list[tuple[list[str], bool]] = []
        self.ffmpeg_install_logs: list[str] = []
        self.ytdlp_logs: list[str] = []

        if self.ffmpeg_missing:
            self.state.status_text = "FFmpeg not found. Install it to ensure merge/extract features work."
            self.playlist_status_message = "FFmpeg not found. Install it for reliable playlist post-processing."

        try:
            self.page.on_platform_brightness_change = self._on_platform_brightness_change
            self._platform_theme_listener_enabled = True
        except Exception:
            self._platform_theme_listener_enabled = False

        self._build_controls()
        self._apply_theme_palette()
        self._apply_quality_options()
        self._apply_playlist_quality_options()
        self._refresh_view()

    def _theme_is_dark(self) -> bool:
        if self.page.theme_mode == ft.ThemeMode.DARK:
            return True
        if self.page.theme_mode == ft.ThemeMode.LIGHT:
            return False
        return self._device_prefers_dark()

    def _brand_logo(self, size: int) -> ft.Image:
        return ft.Image(
            src="assets/icon.png",
            width=size,
            height=size,
            fit=ft.BoxFit.CONTAIN,
        )

    def _platform_name(self) -> str:
        return str(getattr(self.page, "platform", "")).lower()

    def _is_mobile_platform(self) -> bool:
        return "android" in self.platform_name or "ios" in self.platform_name

    def _is_android_platform(self) -> bool:
        return "android" in self.platform_name

    def _is_remote_mobile_web_session(self) -> bool:
        return self.is_mobile_platform and bool(getattr(self.page, "web", False))

    def _supports_directory_picker(self) -> bool:
        if "ios" in self.platform_name:
            return False
        return not self._is_remote_mobile_web_session()

    def _supports_open_folder(self) -> bool:
        system = platform.system().lower()
        return system.startswith("windows") or system == "darwin" or system.startswith("linux")

    def _is_ffmpeg_missing(self) -> bool:
        return shutil.which("ffmpeg") is None

    def _supports_ffmpeg_auto_install(self) -> bool:
        if self.is_android_platform or self._is_remote_mobile_web_session():
            return False
        system = platform.system().lower()
        return system.startswith("linux") or system.startswith("windows") or system == "darwin"

    def _build_ffmpeg_install_hint(self) -> str:
        if self.is_android_platform:
            return "FFmpeg not found. Android builds should bundle FFmpeg or use media that does not require post-processing."
        system = platform.system().lower()
        base = "FFmpeg not found."
        if system.startswith("linux"):
            return f"{base} Install with your package manager, e.g. `sudo apt install ffmpeg`."
        if system == "darwin":
            return f"{base} Install with Homebrew: `brew install ffmpeg`."
        if system.startswith("windows"):
            return f"{base} Install via Winget: `winget install Gyan.FFmpeg`."
        if system == "android":
            return f"{base} Bundle FFmpeg with the app or include a mobile FFmpeg integration."
        return f"{base} Install FFmpeg and ensure it is available in PATH."

    def _device_prefers_dark(self) -> bool:
        brightness = getattr(self.page, "platform_brightness", None)
        if brightness is None:
            return False
        brightness_enum = getattr(ft, "Brightness", None)
        if brightness_enum is not None and brightness == brightness_enum.DARK:
            return True
        if isinstance(brightness, str):
            return brightness.lower() == "dark"
        return False

    def _on_platform_brightness_change(self, _: ft.ControlEvent) -> None:
        if self.page.theme_mode != ft.ThemeMode.SYSTEM:
            return
        self._apply_theme_palette()
        self._page_update()

    def _apply_theme_palette(self) -> None:
        is_dark = self._theme_is_dark()
        self.page.bgcolor = "#0B0B0D" if is_dark else "#FFF7F5"
        self.progress_bar.color = YT_RED
        self.playlist_progress_bar.color = YT_RED

        if hasattr(self, "left_panel"):
            self.left_panel.bgcolor = "#151518" if is_dark else "#FFFFFF"
        if hasattr(self, "right_panel"):
            self.right_panel.bgcolor = "#1D1D21" if is_dark else "#FFFDFC"
        if hasattr(self, "welcome_card"):
            self.welcome_card.bgcolor = "#16161A" if is_dark else "#FFFFFF"
        if hasattr(self, "playlist_card"):
            self.playlist_card.bgcolor = "#16161A" if is_dark else "#FFFFFF"
        if hasattr(self, "history_card"):
            self.history_card.bgcolor = "#16161A" if is_dark else "#FFFFFF"
        if hasattr(self, "about_card"):
            self.about_card.bgcolor = "#16161A" if is_dark else "#FFFFFF"
        self._apply_input_styles()

    def _apply_input_styles(self) -> None:
        is_dark = self._theme_is_dark()
        fill = "#202020" if is_dark else "#FFFFFF"
        border = ft.Colors.with_opacity(0.35, YT_RED)
        focused_border = YT_RED
        inputs = [
            self.url_field,
            self.playlist_url_field,
            self.playlist_range_field,
        ]
        dropdowns = [
            self.quality_dropdown,
            self.playlist_quality_dropdown,
        ]

        for control in inputs:
            control.filled = True
            control.fill_color = fill
            control.border_radius = 14
            control.content_padding = ft.Padding.symmetric(horizontal=14, vertical=12)
            control.border_color = border
            control.focused_border_color = focused_border
            control.focused_border_width = 2

        for control in dropdowns:
            control.filled = True
            control.fill_color = fill
            control.border_radius = 14
            control.content_padding = ft.Padding.symmetric(horizontal=14, vertical=12)
            control.border_color = border
            control.focused_border_color = focused_border
            control.focused_border_width = 2

    def _on_url_commit(self, _: ft.ControlEvent) -> None:
        self.state.url = self.url_field.value.strip() if self.url_field.value else ""

    def _on_load_formats(self, _: ft.ControlEvent) -> None:
        try:
            self.state.url = self.url_field.value.strip() if self.url_field.value else ""
            if not is_valid_url(self.state.url):
                self._set_status("Invalid URL. Please enter a valid link.")
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
        if self._is_remote_mobile_web_session():
            status = (
                "This session runs on Linux host via web. Android storage is not accessible here. "
                "Use a packaged Android build to access phone folders."
            )
            if for_playlist:
                self._set_playlist_status(status)
            else:
                self._set_status(status)
            return

        if not self._supports_open_folder():
            status = "Open folder is not available on this host OS."
            if for_playlist:
                self._set_playlist_status(status)
            else:
                self._set_status(status)
            return

        folder = ensure_download_directory(path)
        if for_playlist:
            self._set_playlist_status(f"Opening host folder: {folder}")
        else:
            self._set_status(f"Opening host folder: {folder}")

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
        if not self._supports_directory_picker():
            if self._is_remote_mobile_web_session():
                status = (
                    "Cannot pick Android storage in web session (`flet run --android`). "
                    "Package and run the app on Android to access device folders."
                )
            else:
                status = "Custom folder selection is not available on this platform."
            if for_playlist:
                self._set_playlist_status(status)
            else:
                self._set_status(status)
            return

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
            self._apply_selected_directory(selected_path, for_playlist=for_playlist)

    def _apply_selected_directory(self, selected_path: str, for_playlist: bool) -> None:
        normalized, used_fallback = resolve_download_directory(selected_path)
        if for_playlist:
            self.state.playlist_save_directory = normalized
            self.playlist_save_dir_text.value = normalized
            if used_fallback:
                self._set_playlist_status(
                    f"Cannot use '{selected_path}' from this session. Using host folder: {normalized}"
                )
            else:
                self._set_playlist_status("Playlist save folder updated on host.")
            self._page_update()
        else:
            self.state.save_directory = normalized
            if used_fallback:
                self._set_status(f"Cannot use '{selected_path}' from this session. Using host folder: {normalized}")
            else:
                self._set_status("Save folder updated on host.")
            self._refresh_view()

    def _on_theme_toggle(self, _: ft.ControlEvent) -> None:
        self.page.theme_mode = ft.ThemeMode.DARK if self.theme_switch.value else ft.ThemeMode.SYSTEM
        self._apply_theme_palette()
        self._page_update()

    def _on_bottom_tab_change(self, event: ft.ControlEvent) -> None:
        self.bottom_tab_index = event.control.selected_index or 0
        self._set_active_panel()
        self._page_update()

    def _apply_bottom_tab_selection(self) -> None:
        if not hasattr(self, "tab_host"):
            return
        if self.bottom_tab_index == 1:
            self.tab_host.content = self.playlist_tab_panel
        elif self.bottom_tab_index == 2:
            self.tab_host.content = self.history_tab_panel
        elif self.bottom_tab_index == 3:
            self.tab_host.content = self.about_tab_panel
        else:
            self.tab_host.content = self.root_container

    def _set_active_panel(self) -> None:
        if self.show_welcome:
            self.tab_host.content = self.welcome_panel
            self.bottom_nav.visible = False
            self.page.scroll = ft.ScrollMode.HIDDEN
            return
        self.bottom_nav.visible = True
        self.page.scroll = ft.ScrollMode.AUTO
        self._apply_bottom_tab_selection()

    def _on_open_app_ui(self, _: ft.ControlEvent) -> None:
        self.show_welcome = False
        self.bottom_tab_index = 0
        self.bottom_nav.selected_index = 0
        self._set_active_panel()
        if self.ffmpeg_missing and not self.ffmpeg_notice_shown:
            self._show_popup(self.ffmpeg_install_hint, ft.Colors.RED_700)
            self.ffmpeg_notice_shown = True
        self._page_update()

    def _on_back_to_welcome(self, _: ft.ControlEvent) -> None:
        self.show_welcome = True
        self.bottom_tab_index = 0
        self.bottom_nav.selected_index = 0
        self._set_active_panel()
        self._page_update()

    def _on_open_developer_dialog(self, _: ft.ControlEvent) -> None:
        self.bottom_tab_index = 3
        self.bottom_nav.selected_index = 3
        self._set_active_panel()
        self._page_update()

    def _on_close_developer_dialog(self, _: ft.ControlEvent) -> None:
        self.bottom_tab_index = 0
        self.bottom_nav.selected_index = 0
        self._set_active_panel()
        self._page_update()

    def _on_close_result_dialog(self, _: ft.ControlEvent) -> None:
        try:
            self.page.pop_dialog()
        except Exception:  # noqa: BLE001
            self.result_dialog.open = False
            self._page_update()

    def _show_result_dialog(self, title: str, message: str) -> None:
        self.result_dialog.title = ft.Text(title)
        self.result_dialog.content = ft.Text(message, selectable=True)
        try:
            self.page.show_dialog(self.result_dialog)
        except Exception:
            self._show_popup(message, ft.Colors.BLUE_GREY_700)

    def _set_status(self, text: str) -> None:
        self.state.status_text = text
        self._refresh_view()

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
        self.pick_dir_btn.disabled = False
        self.open_dir_btn.disabled = not self._supports_open_folder()
        self.playlist_pick_dir_btn.disabled = False
        self.playlist_open_dir_btn.disabled = not self._supports_open_folder()
        self.install_ffmpeg_btn.visible = self.ffmpeg_missing and self.ffmpeg_install_supported
        self.welcome_install_ffmpeg_btn.visible = self.ffmpeg_missing and self.ffmpeg_install_supported
        self.install_ffmpeg_btn.disabled = self.ffmpeg_install_running
        self.welcome_install_ffmpeg_btn.disabled = self.ffmpeg_install_running
        self.recheck_ffmpeg_btn.disabled = self.ffmpeg_install_running
        self.welcome_recheck_ffmpeg_btn.disabled = self.ffmpeg_install_running
        self.view_ffmpeg_log_btn.disabled = not self.ffmpeg_install_logs and not self.ffmpeg_install_running
        self.view_ytdlp_log_btn.disabled = not self.ytdlp_logs
        self.ffmpeg_warning_text.visible = self.ffmpeg_missing
        self.welcome_ffmpeg_warning_text.visible = self.ffmpeg_missing

        self.mode_group.value = self.state.selected_mode
        self.quality_dropdown.value = self.state.selected_quality

        self.title_text.value = self.state.media_title or ""
        self.thumbnail.src = self.state.thumbnail_url
        self.thumbnail.visible = bool(self.state.thumbnail_url)

        self.playlist_save_dir_text.value = self.state.playlist_save_directory
        self.playlist_status_text.value = self.playlist_status_message
        self.playlist_progress_bar.value = self.playlist_progress
        self.playlist_live_status_text.value = self.playlist_live_status
        self.playlist_current_file_text.value = self.playlist_current_file or "-"
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
