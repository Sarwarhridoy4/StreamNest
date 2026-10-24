from __future__ import annotations

import asyncio
import traceback
from pathlib import Path
from typing import TYPE_CHECKING

import flet as ft

from ui.home_view import HomeView

if TYPE_CHECKING:
    from collections.abc import Callable

APP_DIR = Path(__file__).resolve().parent
ICON_PATH = str(APP_DIR / "assets" / "icon.png")


def create_splash_screen() -> tuple[ft.Control, Callable[[ft.Page], None]]:
    """Create a splash screen and return (root_control, start_animation)."""

    logo_container = ft.Container(
        content=ft.Image(
            src=ICON_PATH,
            width=100,
            height=100,
            fit=ft.BoxFit.CONTAIN,
        ),
        animate_scale=ft.Animation(duration=1200, curve=ft.AnimationCurve.EASE_IN_OUT),
        scale=1.0,
        on_click=None,
    )

    status_text = ft.Text(
        "Preparing StreamNest...",
        size=14,
        color=ft.Colors.ON_SURFACE_VARIANT,
        text_align=ft.TextAlign.CENTER,
    )

    progress_ring = ft.ProgressRing(width=32, height=32, stroke_width=3)

    def start_pulse(page: ft.Page) -> None:
        async def pulse() -> None:
            while True:
                logo_container.scale = 1.08
                page.update()
                await asyncio.sleep(0.7)
                logo_container.scale = 1.0
                page.update()
                await asyncio.sleep(0.7)

        _ = asyncio.create_task(pulse())  # noqa: RUF006  # fire-and-forget splash animation

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
                    size=34,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                status_text,
                ft.Container(height=24),
                ft.Row(
                    controls=[progress_ring],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            spacing=16,
        ),
    )

    return root, start_pulse, status_text


async def initialize_app_async(page: ft.Page, status_text: ft.Text) -> None:
    """Initialize the app asynchronously and replace splash screen."""
    try:
        status_text.value = "Loading interface..."
        page.update()
        home = HomeView(page)
        main_ui = home.build()
        page.controls.clear()
        page.add(main_ui)
        page.update()
    except Exception:
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

    # Set window icon for desktop builds
    try:
        page.window_icon = ICON_PATH
    except Exception:
        pass

    platform_name = str(getattr(page, "platform", "")).lower()
    is_desktop = any(name in platform_name for name in ("windows", "linux", "macos"))
    if is_desktop and getattr(page, "window", None) is not None:
        page.window.min_width = 360
        page.window.min_height = 640

    page.scroll = ft.ScrollMode.AUTO

    splash, start_splash_animation, status_text = create_splash_screen()
    page.add(splash)
    page.update()
    start_splash_animation(page)

    page.run_task(initialize_app_async, page, status_text)


if __name__ == "__main__":
    ft.run(main)
