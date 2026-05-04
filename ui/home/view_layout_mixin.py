from __future__ import annotations

import flet as ft

from ui.components import PRIMARY_COLOR, SECONDARY_COLOR, build_header, labeled_control, primary_button, status_chip


class ViewLayoutMixin:
    def build(self) -> ft.Control:
        header = build_header(
            "StreamNest Downloader",
            "Load formats dynamically, then download video/audio or selected playlist items.",
        )

        self.left_panel = ft.Container(
            padding=24,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=[ft.Colors.SURFACE, ft.Colors.with_opacity(0.9, ft.Colors.SURFACE)],
            ),
            border_radius=24,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.24, PRIMARY_COLOR)),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=32,
                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                offset=ft.Offset(0, 12),
            ),
            expand=False,
            content=ft.Column(
                controls=[
                    self.back_to_welcome_btn,
                    ft.Row(
                        controls=[self._brand_logo(36), ft.Text("StreamNest", weight=ft.FontWeight.BOLD, size=20)],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    header,
                    self.ffmpeg_warning_text,
                    self.install_ffmpeg_btn,
                    ft.Row(
                        controls=[self.recheck_ffmpeg_btn, self.view_ffmpeg_log_btn, self.view_ytdlp_log_btn],
                        wrap=True,
                        spacing=8,
                    ),
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
                    self.developer_info_btn,
                ],
                spacing=14,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
        )

        self.right_panel = ft.Container(
            padding=24,
            border_radius=24,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=[ft.Colors.SURFACE_CONTAINER, ft.Colors.SURFACE_CONTAINER_LOWEST],
            ),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.2, PRIMARY_COLOR)),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=28,
                color=ft.Colors.with_opacity(0.12, ft.Colors.BLACK),
                offset=ft.Offset(0, 10),
            ),
            expand=False,
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
                                ft.Text("Recent Downloads", theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
                                self.recent_history_list,
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
        self.root_container = self._build_root_container()
        self.welcome_card = ft.Container(
            width=960,
            padding=ft.padding.symmetric(horizontal=48, vertical=42),
            border_radius=32,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=[ft.Colors.SURFACE, ft.Colors.with_opacity(0.9, ft.Colors.SURFACE)],
            ),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.26, PRIMARY_COLOR)),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=36,
                color=ft.Colors.with_opacity(0.18, ft.Colors.BLACK),
                offset=ft.Offset(0, 16),
            ),
            content=ft.Column(
                controls=[
                    self._brand_logo(76),
                    ft.Text(
                        "Welcome to StreamNest",
                        theme_style=ft.TextThemeStyle.HEADLINE_LARGE,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Download videos, audio, and playlist items with a clean tabbed workflow.",
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    self.welcome_ffmpeg_warning_text,
                    self.welcome_install_ffmpeg_btn,
                    self.welcome_recheck_ffmpeg_btn,
                    ft.Container(height=12),
                    primary_button("Open StreamNest", self._on_open_app_ui),
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        self.welcome_panel = ft.Container(
            expand=True,
            padding=ft.padding.symmetric(horizontal=24, vertical=28),
            content=ft.Column(
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        alignment=ft.Alignment(0, 0),
                        content=self.welcome_card,
                    )
                ],
            ),
        )
        self.playlist_card = ft.Container(
            padding=24,
            border_radius=24,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=[ft.Colors.SURFACE, ft.Colors.with_opacity(0.9, ft.Colors.SURFACE)],
            ),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.2, PRIMARY_COLOR)),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=32,
                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                offset=ft.Offset(0, 12),
            ),
            content=ft.Column(
                controls=[
                    self.playlist_back_btn,
                    ft.Row(
                        controls=[self._brand_logo(34), ft.Text("StreamNest", weight=ft.FontWeight.BOLD, size=18)],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text("Playlist Downloader", theme_style=ft.TextThemeStyle.HEADLINE_SMALL, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "Load playlist metadata, choose entries, and download selected items.",
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
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
                    status_chip("Current file", self.playlist_current_file_text),
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
                spacing=12,
            ),
        )
        self.playlist_tab_panel = ft.Container(
            expand=True,
            padding=16,
            content=ft.Column(
                controls=[
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(
                                col={"xs": 12, "sm": 11, "md": 10, "lg": 9, "xl": 8},
                                content=self.playlist_card,
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=10,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
        )
        self.history_card = ft.Container(
            padding=24,
            border_radius=24,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=[ft.Colors.SURFACE, ft.Colors.with_opacity(0.9, ft.Colors.SURFACE)],
            ),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.2, PRIMARY_COLOR)),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=32,
                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                offset=ft.Offset(0, 12),
            ),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[self._brand_logo(34), ft.Text("Download History", weight=ft.FontWeight.BOLD, size=18)],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(
                        "Encrypted local history of your completed downloads. Tap an entry to view details.",
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(col={"xs": 12, "sm": 7}, content=self.history_summary_text),
                            ft.Container(
                                col={"xs": 12, "sm": 5},
                                alignment=ft.Alignment(1, 0),
                                content=self.clear_history_btn,
                            ),
                        ],
                    ),
                    self.history_tab_list,
                ],
                spacing=12,
                expand=True,
            ),
        )
        self.history_tab_panel = ft.Container(
            expand=True,
            padding=16,
            content=ft.Column(
                controls=[
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(
                                col={"xs": 12, "sm": 11, "md": 10, "lg": 9, "xl": 8},
                                content=self.history_card,
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=10,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
        )
        self.about_card = ft.Container(
            padding=24,
            border_radius=24,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=[ft.Colors.SURFACE, ft.Colors.with_opacity(0.9, ft.Colors.SURFACE)],
            ),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.2, PRIMARY_COLOR)),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=32,
                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                offset=ft.Offset(0, 12),
            ),
            content=ft.Column(
                controls=[
                    self.about_back_btn,
                    ft.Row(
                        controls=[self._brand_logo(34), ft.Text("StreamNest", weight=ft.FontWeight.BOLD, size=18)],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text("About StreamNest", theme_style=ft.TextThemeStyle.HEADLINE_SMALL, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "Desktop media downloader powered by Flet and yt-dlp with single and playlist workflows.",
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Divider(height=18),
                    ft.Text("Official Website", theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
                    ft.Text("https://streamnest-puce.vercel.app", selectable=True),
                    ft.TextButton(content="Open Website", url="https://streamnest-puce.vercel.app"),
                    ft.Divider(height=18),
                    ft.Text("Developer", theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
                    ft.Text("Sarwar Hossain", weight=ft.FontWeight.W_500),
                    ft.Text("https://github.com/Sarwarhridoy4", selectable=True),
                    ft.TextButton(content="Open GitHub", url="https://github.com/Sarwarhridoy4"),
                    ft.Divider(height=18),
                    ft.Text("Highlights", theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
                    ft.Text("• Single video/audio download workflow"),
                    ft.Text("• Playlist item selection and range support"),
                    ft.Text("• Live progress, speed, ETA, and history"),
                ],
                spacing=8,
            ),
        )
        self.about_tab_panel = ft.Container(
            expand=True,
            padding=16,
            content=ft.Column(
                controls=[
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(
                                col={"xs": 12, "sm": 11, "md": 10, "lg": 9, "xl": 8},
                                content=self.about_card,
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=10,
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
        )
        self.tab_host = ft.Container(expand=True, alignment=ft.Alignment(0, 0), content=self.root_container)
        self.bottom_nav = ft.NavigationBar(
            selected_index=self.bottom_tab_index,
            on_change=self._on_bottom_tab_change,
            visible=not self.show_welcome,
            elevation=8,
            height=72,
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.DOWNLOAD, label="Single"),
                ft.NavigationBarDestination(icon=ft.Icons.PLAYLIST_PLAY, label="Playlist"),
                ft.NavigationBarDestination(icon=ft.Icons.HISTORY, label="History"),
                ft.NavigationBarDestination(icon=ft.Icons.INFO_OUTLINE, label="About"),
            ],
        )
        self.page.navigation_bar = self.bottom_nav
        self._set_active_panel()
        self._apply_theme_palette()

        return ft.SafeArea(
            expand=True,
            content=self.tab_host,
        )

    def _build_root_container(self) -> ft.Container:
        return ft.Container(
            expand=True,
            padding=16,
            content=ft.Column(
                controls=[
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(
                                col={"xs": 12, "sm": 11, "md": 10, "lg": 9, "xl": 8},
                                content=self.left_panel,
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(
                                col={"xs": 12, "sm": 11, "md": 10, "lg": 9, "xl": 8},
                                content=self.right_panel,
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=14,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
        )
