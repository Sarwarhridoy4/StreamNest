from __future__ import annotations

import traceback

import flet as ft

from ui.home_view import HomeView


def main(page: ft.Page) -> None:
    try:
        page.title = "StreamNest Media Downloader"
        page.theme = ft.Theme(color_scheme_seed="#FF0000")
        page.dark_theme = ft.Theme(color_scheme_seed="#FF0000")
        page.theme_mode = ft.ThemeMode.SYSTEM
        page.padding = 0

        platform_name = str(getattr(page, "platform", "")).lower()
        is_desktop = any(name in platform_name for name in ("windows", "linux", "macos"))
        if is_desktop and getattr(page, "window", None) is not None:
            page.window.min_width = 360
            page.window.min_height = 640

        page.scroll = ft.ScrollMode.AUTO

        home = HomeView(page)
        page.add(home.build())
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        page.clean()
        page.scroll = ft.ScrollMode.AUTO
        page.add(
            ft.Column(
                controls=[
                    ft.Text("Failed to initialize UI", weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                    ft.Text(
                        "An unexpected error occurred during startup. Please check the terminal logs.",
                        selectable=True,
                    ),
                ],
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            )
        )
        page.update()


if __name__ == "__main__":
    ft.run(main)
