from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse
from uuid import uuid4

import flet as ft

from services.downloader import DownloadResult
from state.app_state import HistoryEntry
from ui.components import PRIMARY_COLOR


class HistoryMixin:
    def _append_download_history(self, result: DownloadResult) -> None:
        source_url = self.playlist_url_field.value.strip() if self.active_download_context == "playlist" else self.state.url
        target_dir = (
            self.state.playlist_save_directory if self.active_download_context == "playlist" else self.state.save_directory
        )
        title = self.state.media_title or source_url or "Download"
        if self.active_download_context == "playlist":
            title = f"Playlist download ({len(self.playlist_selected_indices)} item(s))"
        entry = HistoryEntry(
            id=uuid4().hex,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            title=title,
            url=source_url,
            platform=self._detect_platform_label(source_url),
            mode="playlist" if self.active_download_context == "playlist" else self.state.selected_mode,
            quality=self.playlist_selected_quality if self.active_download_context == "playlist" else self.state.selected_quality,
            save_directory=target_dir,
            context=self.active_download_context,
            status="success",
            message=result.message,
        )
        self.state.append_history(entry)
        self._persist_history()
        self._render_history()

    def _persist_history(self) -> None:
        try:
            self.history_store.save(self.state.history)
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Failed to persist encrypted history: {exc}")

    def _detect_platform_label(self, url: str) -> str:
        host = urlparse(url).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        if "youtube.com" in host or "youtu.be" in host:
            return "YouTube"
        if "facebook.com" in host or "fb.watch" in host:
            return "Facebook"
        if "instagram.com" in host:
            return "Instagram"
        if "tiktok.com" in host:
            return "TikTok"
        if "twitter.com" in host or "x.com" in host:
            return "X/Twitter"
        if not host:
            return "Unknown"
        domain_parts = host.split(".")
        return domain_parts[-2].upper() if len(domain_parts) >= 2 else host.upper()

    def _render_history(self) -> None:
        recent_entries = self.state.history[:6]
        self.recent_history_list.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(f"{entry.platform} • {entry.title}", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(entry.timestamp, size=11, color=ft.Colors.ON_SURFACE_VARIANT),
                    ],
                    spacing=2,
                ),
                padding=10,
                border_radius=10,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            )
            for entry in recent_entries
        ]

        self.history_summary_text.value = (
            f"{len(self.state.history)} item(s) saved"
            if self.state.history
            else "No downloads yet."
        )
        self.history_tab_list.controls = [self._build_history_row(entry) for entry in self.state.history]

    def _build_history_row(self, entry: HistoryEntry) -> ft.Control:
        return ft.Container(
            padding=12,
            border_radius=12,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.12, PRIMARY_COLOR)),
            content=ft.ListTile(
                leading=ft.Icon(ft.Icons.MOVIE_CREATION_OUTLINED if entry.context == "single" else ft.Icons.PLAYLIST_PLAY),
                title=ft.Text(f"{entry.platform} • {entry.title}", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                subtitle=ft.Text(
                    f"{entry.timestamp} • {entry.mode.upper()} • {entry.quality}",
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                on_click=lambda _: self._on_open_history_details(entry),
            ),
        )

    def _on_open_history_details(self, entry: HistoryEntry) -> None:
        details = [
            f"Title: {entry.title}",
            f"Platform: {entry.platform}",
            f"Timestamp: {entry.timestamp}",
            f"Context: {entry.context}",
            f"Mode: {entry.mode}",
            f"Quality: {entry.quality}",
            f"Save folder: {entry.save_directory}",
            f"URL: {entry.url or '-'}",
            f"Result: {entry.message}",
        ]
        self.history_details_dialog.title = ft.Text("History Details")
        self.history_details_dialog.content = ft.Text("\n".join(details), selectable=True)
        try:
            self.page.show_dialog(self.history_details_dialog)
        except Exception:
            self._show_popup("Unable to open details dialog.", ft.Colors.RED_700)

    def _on_erase_history(self, _: ft.ControlEvent) -> None:
        try:
            self.page.show_dialog(self.confirm_clear_history_dialog)
        except Exception:
            self._show_popup("Unable to open confirmation dialog.", ft.Colors.RED_700)

    def _on_confirm_erase_history(self, _: ft.ControlEvent) -> None:
        self.state.clear_history()
        try:
            self.history_store.clear()
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Failed to erase encrypted history: {exc}")
        self._render_history()
        try:
            self.page.pop_dialog()
        except Exception:
            self.confirm_clear_history_dialog.open = False
        self._show_popup("History erased.", ft.Colors.BLUE_GREY_700)
        self._refresh_view()
