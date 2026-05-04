from __future__ import annotations

import flet as ft

from ui.components import primary_button, secondary_button


class ControlLayoutMixin:
    def _build_controls(self) -> None:
        self.url_field = ft.TextField(
            label="Media URL",
            hint_text="Paste video/audio URL",
            on_submit=self._on_url_commit,
            on_blur=self._on_url_commit,
            expand=True,
        )

        self.load_formats_btn = secondary_button("Load Formats", self._on_load_formats, icon=ft.Icons.SEARCH)
        self.open_playlist_btn = secondary_button("Open Playlist Tab", self._on_open_playlist_dialog, icon=ft.Icons.PLAYLIST_PLAY)

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
        self.pick_dir_btn = secondary_button("Choose Save Folder", self._on_pick_directory, icon=ft.Icons.FOLDER_OPEN)
        self.open_dir_btn = secondary_button("Open Folder", self._on_open_directory, icon=ft.Icons.FOLDER)

        self.progress_bar = ft.ProgressBar(value=0.0)
        self.status_text = ft.Text("Idle")
        self.speed_text = ft.Text("", selectable=False)
        self.eta_text = ft.Text("", selectable=False)
        self.size_text = ft.Text("", selectable=False)
        self.ffmpeg_warning_text = ft.Text(
            self.ffmpeg_install_hint,
            color=ft.Colors.RED_700,
            selectable=True,
            visible=self.ffmpeg_missing,
        )
        self.install_ffmpeg_btn = secondary_button("Install FFmpeg", self._on_install_ffmpeg)
        self.install_ffmpeg_btn.visible = self.ffmpeg_missing and self.ffmpeg_install_supported
        self.recheck_ffmpeg_btn = ft.TextButton(content="Re-check FFmpeg", on_click=self._on_recheck_ffmpeg)
        self.view_ffmpeg_log_btn = ft.TextButton(content="View Install Log", on_click=self._on_open_ffmpeg_log)
        self.view_ytdlp_log_btn = ft.TextButton(content="View yt-dlp Log", on_click=self._on_open_ytdlp_log)
        self.welcome_ffmpeg_warning_text = ft.Text(
            self.ffmpeg_install_hint,
            color=ft.Colors.RED_700,
            selectable=True,
            text_align=ft.TextAlign.CENTER,
            visible=self.ffmpeg_missing,
        )
        self.welcome_install_ffmpeg_btn = secondary_button("Install FFmpeg", self._on_install_ffmpeg)
        self.welcome_install_ffmpeg_btn.visible = self.ffmpeg_missing and self.ffmpeg_install_supported
        self.welcome_recheck_ffmpeg_btn = ft.TextButton(content="Re-check FFmpeg", on_click=self._on_recheck_ffmpeg)

        self.download_btn = primary_button("Download", self._on_download, icon=ft.Icons.DOWNLOAD)
        self.cancel_btn = secondary_button("Cancel", self._on_cancel, disabled=True, icon=ft.Icons.CANCEL)
        self.developer_info_btn = secondary_button("About Developer", self._on_open_developer_dialog, icon=ft.Icons.INFO)
        self.back_to_welcome_btn = ft.TextButton(
            content="Back to Welcome",
            on_click=self._on_back_to_welcome,
        )
        self.playlist_back_btn = ft.TextButton(
            content="Back to Welcome",
            on_click=self._on_back_to_welcome,
        )
        self.about_back_btn = ft.TextButton(
            content="Back to Welcome",
            on_click=self._on_back_to_welcome,
        )
        self.theme_switch = ft.Switch(label="Force dark theme", value=False, on_change=self._on_theme_toggle)

        self.thumbnail = ft.Image(
            src="",
            fit=ft.BoxFit.COVER,
            border_radius=12,
            visible=False,
            expand=True,
        )
        self.title_text = ft.Text("", weight=ft.FontWeight.W_500, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)

        self.recent_history_list = ft.ListView(spacing=6, auto_scroll=False, expand=True)
        self.history_tab_list = ft.ListView(spacing=10, auto_scroll=False, expand=True)
        self.history_summary_text = ft.Text("No downloads yet.", color=ft.Colors.ON_SURFACE_VARIANT)
        self.clear_history_btn = secondary_button("Erase History", self._on_erase_history, icon=ft.Icons.DELETE_FOREVER)

        # Playlist controls
        self.playlist_url_field = ft.TextField(
            label="Playlist URL",
            hint_text="Paste playlist URL",
            expand=True,
        )
        self.playlist_range_field = ft.TextField(
            label="Range",
            hint_text="Examples: 1-5 or 1,3,7-10 (leave empty for all)",
            expand=True,
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
        self.playlist_pick_dir_btn = secondary_button("Choose Save Folder", self._on_pick_playlist_directory, icon=ft.Icons.FOLDER_OPEN)
        self.playlist_open_dir_btn = secondary_button("Open Folder", self._on_open_playlist_directory, icon=ft.Icons.FOLDER)

        self.playlist_status_text = ft.Text(self.playlist_status_message)
        self.playlist_progress_bar = ft.ProgressBar(value=0.0)
        self.playlist_live_status_text = ft.Text(self.playlist_live_status)
        self.playlist_current_file_text = ft.Text(self.playlist_current_file, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
        self.playlist_speed_text = ft.Text("-", selectable=False)
        self.playlist_eta_text = ft.Text("-", selectable=False)
        self.playlist_items_list = ft.ListView(spacing=4, auto_scroll=True, height=220)

        self.playlist_load_btn = primary_button("Load Playlist", self._on_load_playlist, icon=ft.Icons.LIST)
        self.playlist_download_btn = primary_button("Download Selected", self._on_playlist_download, icon=ft.Icons.DOWNLOAD)
        self.playlist_select_all_btn = ft.TextButton(content="Select all", on_click=self._on_playlist_select_all)
        self.playlist_clear_btn = ft.TextButton(content="Clear", on_click=self._on_playlist_clear)
        self.result_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Download Status"),
            content=ft.Text(""),
            actions=[ft.TextButton(content="OK", on_click=self._on_close_result_dialog)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.history_details_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Download Details"),
            content=ft.Text(""),
            actions=[ft.TextButton(content="Close", on_click=self._on_close_result_dialog)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.confirm_clear_history_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Erase Download History"),
            content=ft.Text("This will permanently remove all saved history entries."),
            actions=[
                ft.TextButton(content="Cancel", on_click=self._on_close_result_dialog),
                ft.TextButton(content="Erase", on_click=self._on_confirm_erase_history),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.ffmpeg_password_field = ft.TextField(
            label="System password",
            hint_text="Needed for privileged install commands",
            password=True,
            can_reveal_password=True,
            autofocus=True,
        )
        self.ffmpeg_install_confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Install FFmpeg"),
            content=ft.Text(""),
            actions=[
                ft.TextButton(content="Cancel", on_click=self._on_close_result_dialog),
                ft.TextButton(content="Install", on_click=self._on_ffmpeg_install_confirmed),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.ffmpeg_password_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Administrator Password Required"),
            content=ft.Column(
                controls=[
                    ft.Text("Enter your password to run privileged install commands."),
                    self.ffmpeg_password_field,
                ],
                tight=True,
                spacing=8,
            ),
            actions=[
                ft.TextButton(content="Cancel", on_click=self._on_close_result_dialog),
                ft.TextButton(content="Continue", on_click=self._on_ffmpeg_password_submit),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.ffmpeg_log_text = ft.Text("", selectable=True)
        self.ffmpeg_log_dialog = ft.AlertDialog(
            modal=False,
            title=ft.Text("FFmpeg Install Log"),
            content=ft.Container(
                width=760,
                height=360,
                border_radius=10,
                padding=10,
                bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                content=ft.Column(
                    controls=[self.ffmpeg_log_text],
                    scroll=ft.ScrollMode.ALWAYS,
                    expand=True,
                ),
            ),
            actions=[ft.TextButton(content="Close", on_click=self._on_close_ffmpeg_log_dialog)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.ytdlp_log_text = ft.Text("", selectable=True)
        self.ytdlp_log_dialog = ft.AlertDialog(
            modal=False,
            title=ft.Text("yt-dlp Log"),
            content=ft.Container(
                width=760,
                height=360,
                border_radius=10,
                padding=10,
                bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                content=ft.Column(
                    controls=[self.ytdlp_log_text],
                    scroll=ft.ScrollMode.ALWAYS,
                    expand=True,
                ),
            ),
            actions=[ft.TextButton(content="Close", on_click=self._on_close_ytdlp_log_dialog)],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._apply_input_styles()

