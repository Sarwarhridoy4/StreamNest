from __future__ import annotations

import traceback
from typing import Callable

import flet as ft

from ui.home_view import HomeView


def create_splash_screen() -> tuple[ft.Control, Callable[[], None]]:
    """Create a splash screen and return (root_control, start_animation)."""
    import asyncio

    logo_container = ft.Container(
        content=ft.Image(
            src="assets/icon.png",
            width=120,
            height=120,
            fit=ft.BoxFit.CONTAIN,
        ),
        animate_scale=ft.Animation(duration=1500, curve=ft.AnimationCurve.EASE_IN_OUT),
        scale=1.0,
        on_click=None,
    )

    def start_pulse() -> None:
        async def pulse() -> None:
            while True:
                logo_container.scale = 1.1
                logo_container.update()
                await asyncio.sleep(0.75)
                logo_container.scale = 1.0
                logo_container.update()
                await asyncio.sleep(0.75)

        asyncio.create_task(pulse())

    root = ft.Container(
        expand=True,
        alignment=ft.Alignment(0, 0),
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                logo_container,
                ft.Text(
                    "StreamNest",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Loading...",
                    size=16,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=20),
                ft.ProgressRing(width=40, height=40),
            ],
            spacing=16,
        ),
    )

    return root, start_pulse


async def initialize_app_async(page: ft.Page) -> None:
    """Initialize the app asynchronously and replace splash screen."""
    try:
        home = HomeView(page)
        main_ui = home.build()
        page.controls.clear()
        page.add(main_ui)
        page.update()
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        page.controls.clear()
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


def main(page: ft.Page) -> None:
    page.title = "StreamNest Media Downloader"
    page.theme = ft.Theme(color_scheme_seed="#6366f1")
    page.dark_theme = ft.Theme(color_scheme_seed="#6366f1")
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.padding = 0

    platform_name = str(getattr(page, "platform", "")).lower()
    is_desktop = any(name in platform_name for name in ("windows", "linux", "macos"))
    if is_desktop and getattr(page, "window", None) is not None:
        page.window.min_width = 360
        page.window.min_height = 640

    page.scroll = ft.ScrollMode.AUTO

    splash, start_splash_animation = create_splash_screen()
    page.add(splash)
    page.update()
    start_splash_animation()

    page.run_task(initialize_app_async, page)


if __name__ == "__main__":
    ft.run(main)
