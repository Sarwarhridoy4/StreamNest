from __future__ import annotations

import flet as ft

YT_RED = "#FF0000"
YT_DARK_RED = "#CC0000"


def build_header(title: str, subtitle: str) -> ft.Column:
    return ft.Column(
        controls=[
            ft.Text(title, theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM, weight=ft.FontWeight.BOLD),
            ft.Text(subtitle, color=ft.Colors.ON_SURFACE_VARIANT),
        ],
        spacing=4,
    )


def labeled_control(label: str, control: ft.Control) -> ft.Column:
    return ft.Column(
        controls=[
            ft.Text(label, weight=ft.FontWeight.W_500),
            control,
        ],
        spacing=6,
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
        border_radius=8,
        bgcolor=ft.Colors.with_opacity(0.08, YT_RED),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.2, YT_RED)),
    )


def primary_button(text: str, on_click) -> ft.Button:  # type: ignore[no-untyped-def]
    return ft.Button(
        content=text,
        on_click=on_click,
        style=ft.ButtonStyle(
            bgcolor={ft.ControlState.DEFAULT: YT_RED, ft.ControlState.DISABLED: ft.Colors.GREY_400},
            color={ft.ControlState.DEFAULT: ft.Colors.WHITE, ft.ControlState.DISABLED: ft.Colors.WHITE_70},
            shape=ft.RoundedRectangleBorder(radius=16),
            padding=ft.Padding.symmetric(horizontal=18, vertical=14),
        ),
    )


def secondary_button(text: str, on_click, disabled: bool = False) -> ft.OutlinedButton:  # type: ignore[no-untyped-def]
    return ft.OutlinedButton(
        content=text,
        on_click=on_click,
        disabled=disabled,
        style=ft.ButtonStyle(
            color={ft.ControlState.DEFAULT: YT_DARK_RED, ft.ControlState.DISABLED: ft.Colors.GREY_500},
            side={
                ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.with_opacity(0.5, YT_RED)),
                ft.ControlState.DISABLED: ft.BorderSide(1, ft.Colors.GREY_400),
            },
            shape=ft.RoundedRectangleBorder(radius=16),
            padding=ft.Padding.symmetric(horizontal=18, vertical=14),
        ),
    )
