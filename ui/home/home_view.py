from __future__ import annotations

import os
from pathlib import Path
import platform
import subprocess
import webbrowser
from typing import Callable

import flet as ft

from services.downloader import DownloaderService
from services.format_extractor import (
    FormatExtractor,
    PlaylistEntry,
    QualityOption,
)
from state.app_state import AppState
from utils.file_manager import ensure_download_directory, resolve_download_directory
from utils.history_store import HistoryStore
from utils.validators import is_valid_url
from ui.home.download_mixin import DownloadMixin
from ui.home.ffmpeg_install_mixin import FfmpegInstallMixin
from ui.home.history_mixin import HistoryMixin
from ui.home.playlist_mixin import PlaylistMixin
from ui.home.control_layout_mixin import ControlLayoutMixin
from ui.home.view_layout_mixin import ViewLayoutMixin
from ui.home.platform_utils import PlatformUtils
from ui.home.ffmpeg_utils import FFmpegUtils
from ui.home.theme_manager import ThemeManager


class HomeView(
    FfmpegInstallMixin,
    DownloadMixin,
    PlaylistMixin,
    HistoryMixin,
    ControlLayoutMixin,
    ViewLayoutMixin,
):
    def __init__(self, page: ft.Page) -> None:
        """Initialize the HomeView with all necessary components and state."""
        import sys

        self.page = page

        # Initialize utility classes
        self.platform_utils = PlatformUtils(page)
        self.ffmpeg_utils = FFmpegUtils(self.platform_utils)
        self.theme_manager = ThemeManager(self)

        # Initialize core application state and services
        self._initialize_core_state()
        self._initialize_services()

        # Initialize UI state and platform-specific properties
        self._initialize_ui_state()
        self._initialize_ffmpeg_state()

        # Setup platform theme listener and initial UI
        self.theme_manager.setup_theme_listener()
        self._initialize_ui_components()

    def _initialize_core_state(self) -> None:
        """Initialize core application state including directories and history."""
        default_dir = ensure_download_directory(None)
        self.state = AppState(save_directory=default_dir, playlist_save_directory=default_dir)

        # Initialize history storage but defer loading
        self.history_store = HistoryStore()
        self.state.set_history([])  # Start with empty history

    def _initialize_services(self) -> None:
        """Initialize core services for downloading and format extraction."""
        self.downloader = DownloaderService()
        self.extractor = FormatExtractor()

    def _initialize_ui_state(self) -> None:
        """Initialize UI state variables for quality options and playlist management."""
        # Quality options for single downloads
        self.quality_options: list[QualityOption] = [
            QualityOption(label="Best", value="best"),
            QualityOption(label="Worst", value="worst"),
        ]

        # Quality options for playlist downloads
        self.playlist_quality_options: list[QualityOption] = [
            QualityOption(label="Best", value="best"),
            QualityOption(label="Worst", value="worst"),
        ]

        # Playlist-specific state variables
        self.playlist_selected_quality = "best"
        self.playlist_entries: list[PlaylistEntry] = []
        self.playlist_selected_indices: set[int] = set()
        self.playlist_status_message = "Load playlist to choose items."
        self.active_download_context = "single"

        # Playlist progress tracking
        self.playlist_progress = 0.0
        self.playlist_speed = ""
        self.playlist_eta = ""
        self.playlist_live_status = "Idle"
        self.playlist_current_file = "-"

        # Navigation and view state
        self.bottom_tab_index = 0
        self.show_welcome = True

    # Platform properties are now handled by PlatformUtils

    def _initialize_ffmpeg_state(self) -> None:
        """Initialize FFmpeg-related state and detection."""
        self.ffmpeg_notice_shown = False
        self.ffmpeg_missing = False  # Will be checked later
        self.ffmpeg_install_hint = "Checking FFmpeg availability..."
        self.ffmpeg_install_supported = self.ffmpeg_utils.supports_ffmpeg_auto_install()
        self.ffmpeg_install_running = False
        self.pending_ffmpeg_install_plan: list[tuple[list[str], bool]] = []
        self.ffmpeg_install_logs: list[str] = []
        self.ytdlp_logs: list[str] = []

    # Theme listener setup is now handled by ThemeManager

    def _initialize_ui_components(self) -> None:
        """Initialize and configure all UI components and apply initial theming."""
        self._build_controls()
        self.theme_manager.apply_theme_palette()
        self._apply_quality_options()
        self._apply_playlist_quality_options()
        self._refresh_view()

        # Load history and check FFmpeg asynchronously after UI is ready
        self.page.run_task(self._load_history_async)
        self.page.run_task(self._check_ffmpeg_async)

    def _brand_logo(self, size: int) -> ft.Image:
        """Create and return the brand logo image."""
        return ft.Image(
            src="assets/icon.png",
            width=size,
            height=size,
            fit=ft.BoxFit.CONTAIN,
        )

    def _get_theme_icon(self) -> str:
        """Get the appropriate icon for the current theme mode."""
        if self.page.theme_mode == ft.ThemeMode.DARK:
            return ft.Icons.BRIGHTNESS_4  # Dark theme active
        elif self.page.theme_mode == ft.ThemeMode.LIGHT:
            return ft.Icons.BRIGHTNESS_7  # Light theme active
        else:  # SYSTEM
            return ft.Icons.BRIGHTNESS_AUTO  # System theme (auto)

    def _on_platform_brightness_change(self, _: ft.ControlEvent) -> None:
        """Handle platform brightness changes to update theme automatically."""
        if self.page.theme_mode != ft.ThemeMode.SYSTEM:
            return
        self.theme_manager.apply_theme_palette()
        self._page_update()

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
        folder = ensure_download_directory(path)

        # Check if folder exists
        if not os.path.exists(folder):
            status = f"Folder does not exist: {folder}"
            print(f"DEBUG: {status}")
            if for_playlist:
                self._set_playlist_status(status)
            else:
                self._set_status(status)
            return

        if for_playlist:
            self._set_playlist_status(f"Opening playlist folder: {folder}")
        else:
            self._set_status(f"Opening download folder: {folder}")

        # Run file manager opening synchronously (not in a thread)
        # GUI applications need to run in the main thread
        try:
            system = platform.system().lower()

            if system.startswith("windows"):
                os.startfile(folder)  # type: ignore[attr-defined]

            elif system == "darwin":
                subprocess.run(["open", folder], check=False)  # noqa: S603,S607

            else:  # Linux/Unix
                # Check if we have a GUI environment
                has_display = 'DISPLAY' in os.environ or 'WAYLAND_DISPLAY' in os.environ
                if not has_display:
                    status = "Cannot open folder: No GUI display detected"
                    if for_playlist:
                        self._set_playlist_status(status)
                    else:
                        self._set_status(status)
                    return
                # Check if we have a GUI environment
                has_display = 'DISPLAY' in os.environ or 'WAYLAND_DISPLAY' in os.environ
                if not has_display:
                    status = "Cannot open folder: No GUI display detected"
                    if for_playlist:
                        self._set_playlist_status(status)
                    else:
                        self._set_status(status)
                    return

                # Try xdg-open first (most standard approach)
                try:
                    result = subprocess.run(
                        ["xdg-open", folder],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        return  # Success
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass

                # Fallback to common file managers
                file_managers = [
                    ["nautilus", "--no-desktop", folder],  # GNOME Files
                    ["dolphin", folder],  # KDE Dolphin
                    ["thunar", folder],  # XFCE Thunar
                    ["nemo", folder],    # Cinnamon Nemo
                    ["pcmanfm", folder], # LXDE PCManFM
                ]

                for cmd in file_managers:
                    try:
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            return  # Success
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        continue

                # Last resort: try webbrowser as fallback
                try:
                    if os.name == 'nt':
                        file_url = f"file:///{folder.replace('\\', '/')}"
                    else:
                        file_url = f"file://{folder}"
                    webbrowser.open(file_url)
                except Exception:
                    raise Exception("No file manager found and webbrowser fallback failed")

        except subprocess.TimeoutExpired:
            error_msg = "Folder opening timed out"
            if for_playlist:
                self._set_playlist_status(f"Open folder failed: {error_msg}")
            else:
                self._set_status(f"Open folder failed: {error_msg}")
        except Exception as exc:  # noqa: BLE001
            error_msg = str(exc)
            if for_playlist:
                self._set_playlist_status(f"Open folder failed: {error_msg}")
            else:
                self._set_status(f"Open folder failed: {error_msg}")

    async def _pick_directory(self, for_playlist: bool) -> None:
        if not self.platform_utils.supports_directory_picker():
            if self.platform_utils.is_remote_mobile_web_session():
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
        """Cycle through theme modes: System → Dark → Light → System."""
        current_mode = self.page.theme_mode

        if current_mode == ft.ThemeMode.SYSTEM:
            self.page.theme_mode = ft.ThemeMode.DARK
        elif current_mode == ft.ThemeMode.DARK:
            self.page.theme_mode = ft.ThemeMode.LIGHT
        elif current_mode == ft.ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.SYSTEM
        else:
            # Default to system if unknown state
            self.page.theme_mode = ft.ThemeMode.SYSTEM

        self.theme_manager.apply_theme_palette()
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
        supports_open = self.platform_utils.supports_open_folder()

        self.open_dir_btn.disabled = not supports_open
        self.playlist_pick_dir_btn.disabled = False
        self.playlist_open_dir_btn.disabled = not supports_open
        self.install_ffmpeg_btn.visible = self.ffmpeg_missing and self.ffmpeg_install_supported
        self.welcome_install_ffmpeg_btn.visible = self.ffmpeg_missing and self.ffmpeg_install_supported
        self.install_ffmpeg_btn.disabled = self.ffmpeg_install_running
        self.welcome_install_ffmpeg_btn.disabled = self.ffmpeg_install_running
        self.recheck_ffmpeg_btn.disabled = self.ffmpeg_install_running
        self.welcome_recheck_ffmpeg_btn.disabled = self.ffmpeg_install_running
        self.view_ffmpeg_log_btn.disabled = not self.ffmpeg_install_logs and not self.ffmpeg_install_running
        self.view_ytdlp_log_btn.disabled = not self.ytdlp_logs
        self.ffmpeg_warning_text.visible = True
        self.ffmpeg_warning_text.color = ft.Colors.GREEN_700 if not self.ffmpeg_missing else ft.Colors.RED_700
        self.welcome_ffmpeg_warning_text.visible = True
        self.welcome_ffmpeg_warning_text.color = ft.Colors.GREEN_700 if not self.ffmpeg_missing else ft.Colors.RED_700

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

    async def _load_history_async(self) -> None:
        """Load history in background after UI initialization."""
        try:
            history = self.history_store.load()
            self.state.set_history(history)
            self._render_history()
            self._page_update()
        except Exception:  # noqa: BLE001
            # History loading failed, but don't crash the app
            pass

    async def _check_ffmpeg_async(self) -> None:
        """Check FFmpeg availability in background after UI initialization."""
        try:
            self.ffmpeg_missing = self.ffmpeg_utils.is_ffmpeg_missing()
            if self.ffmpeg_missing:
                self.ffmpeg_install_hint = self.ffmpeg_utils.build_ffmpeg_install_hint()
                self.state.status_text = "FFmpeg not found. Install it to ensure merge/extract features work."
                self.playlist_status_message = "FFmpeg not found. Install it for reliable playlist post-processing."
            else:
                version = self.ffmpeg_utils.get_ffmpeg_version()
                self.ffmpeg_install_hint = f"FFmpeg {version} detected."
                if not self.state.status_text:
                    self.state.status_text = "Ready."
                if not self.playlist_status_message:
                    self.playlist_status_message = "Ready."
            self._refresh_view()
        except Exception:  # noqa: BLE001
            self.ffmpeg_missing = True
            self.ffmpeg_install_hint = "Unable to check FFmpeg status."
            self._refresh_view()

    def _page_update(self) -> None:
        self.page.update()
