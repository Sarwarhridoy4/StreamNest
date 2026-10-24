from __future__ import annotations

import flet as ft

PRIMARY_COLOR = "#6366f1"
SECONDARY_COLOR = "#8b5cf6"
PRIMARY_DARK = "#4f46e5"
SECONDARY_DARK = "#7c3aed"

SUCCESS_COLOR = "#10b981"
ERROR_COLOR = "#ef4444"
WARNING_COLOR = "#f59e0b"
INFO_COLOR = "#3b82f6"


def build_header(title: str, subtitle: str) -> ft.Column:
    return ft.Column(
        controls=[
            ft.Text(title, theme_style=ft.TextThemeStyle.HEADLINE_LARGE, weight=ft.FontWeight.BOLD, size=28),
            ft.Text(subtitle, color=ft.Colors.ON_SURFACE_VARIANT, size=16, weight=ft.FontWeight.W_400),
        ],
        spacing=6,
    )


def labeled_control(label: str, control: ft.Control) -> ft.Column:
    return ft.Column(
        controls=[
            ft.Text(label, weight=ft.FontWeight.W_500, size=14, color=ft.Colors.ON_SURFACE),
            control,
        ],
        spacing=8,
        expand=True,
    )


def status_chip(label: str, value_control: ft.Control) -> ft.Container:
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(label, size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                value_control,
            ],
            spacing=2,
        ),
        padding=8,
        border_radius=12,
        bgcolor=ft.Colors.with_opacity(0.08, PRIMARY_COLOR),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.3, PRIMARY_COLOR)),
    )


def section_divider(label: str | None = None) -> ft.Control:
    """A subtle section divider, optionally with a label."""
    if label:
        return ft.Row(
            controls=[
                ft.Container(expand=True, height=1, bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.ON_SURFACE)),
                ft.Text(label, size=11, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Container(expand=True, height=1, bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.ON_SURFACE)),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )
    return ft.Container(height=1, bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.ON_SURFACE))


def primary_button(text: str, on_click, icon: str | None = None, *, loading: bool = False) -> ft.Button:  # type: ignore[no-untyped-def]
    content_controls: list[ft.Control] = []
    if loading:
        content_controls.append(
            ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.WHITE)
        )
    elif icon:
        content_controls.append(ft.Icon(icon, size=18))
    content_controls.append(ft.Text(text, size=14, weight=ft.FontWeight.W_500))
    content = ft.Row(
        controls=content_controls,
        spacing=8,
        alignment=ft.MainAxisAlignment.CENTER,
    )
    return ft.Button(
        content=content,
        on_click=None if loading else on_click,
        disabled=loading,
        style=ft.ButtonStyle(
            bgcolor={
                ft.ControlState.DEFAULT: PRIMARY_COLOR,
                ft.ControlState.HOVERED: PRIMARY_DARK,
                ft.ControlState.DISABLED: ft.Colors.GREY_500,
            },
            color={ft.ControlState.DEFAULT: ft.Colors.WHITE, ft.ControlState.DISABLED: ft.Colors.WHITE_70},
            shape=ft.RoundedRectangleBorder(radius=20),
            padding=ft.Padding.symmetric(horizontal=20, vertical=16),
        ),
    )


def secondary_button(text: str, on_click, disabled: bool = False, icon: str | None = None, *, loading: bool = False) -> ft.OutlinedButton:  # type: ignore[no-untyped-def]  # noqa: FBT002
    content_controls: list[ft.Control] = []
    if loading:
        content_controls.append(
            ft.ProgressRing(width=14, height=14, stroke_width=2, color=SECONDARY_COLOR)
        )
    elif icon:
        content_controls.append(ft.Icon(icon, size=16))
    content_controls.append(ft.Text(text, size=13, weight=ft.FontWeight.W_400))
    content = ft.Row(
        controls=content_controls,
        spacing=6,
        alignment=ft.MainAxisAlignment.CENTER,
    )
    return ft.OutlinedButton(
        content=content,
        on_click=None if loading else on_click,
        disabled=disabled or loading,
        style=ft.ButtonStyle(
            color={
                ft.ControlState.DEFAULT: SECONDARY_COLOR,
                ft.ControlState.HOVERED: SECONDARY_DARK,
                ft.ControlState.DISABLED: ft.Colors.GREY_500,
            },
            side={
                ft.ControlState.DEFAULT: ft.BorderSide(2, ft.Colors.with_opacity(0.6, SECONDARY_COLOR)),
                ft.ControlState.DISABLED: ft.BorderSide(1, ft.Colors.GREY_400),
            },
            shape=ft.RoundedRectangleBorder(radius=20),
            padding=ft.Padding.symmetric(horizontal=20, vertical=16),
        ),
    )


class ToastManager:
    """Shows temporary snackbar-style toast notifications."""

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self._snack_bar: ft.SnackBar | None = None

    def show(
        self,
        message: str,
        *,
        toast_type: str = "info",
        duration: int = 3000,
    ) -> None:
        """Display a toast notification.

        toast_type: one of "info", "success", "warning", "error".
        """
        color_map = {
            "success": SUCCESS_COLOR,
            "error": ERROR_COLOR,
            "warning": WARNING_COLOR,
            "info": INFO_COLOR,
        }
        icon_map = {
            "success": ft.Icons.CHECK_CIRCLE,
            "error": ft.Icons.ERROR,
            "warning": ft.Icons.WARNING,
            "info": ft.Icons.INFO,
        }

        self._snack_bar = ft.SnackBar(
            content=ft.Row(
                controls=[
                    ft.Icon(icon_map.get(toast_type, ft.Icons.INFO), size=18, color=ft.Colors.WHITE),
                    ft.Text(message, size=13, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=color_map.get(toast_type, INFO_COLOR),
            duration=duration,
        )
        self.page.overlay.append(self._snack_bar)
        self._snack_bar.open = True
        self.page.update()
