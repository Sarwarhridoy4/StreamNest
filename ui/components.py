from __future__ import annotations

import flet as ft

PRIMARY_COLOR = "#6366f1"
SECONDARY_COLOR = "#8b5cf6"
PRIMARY_DARK = "#4f46e5"
SECONDARY_DARK = "#7c3aed"


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


def primary_button(text: str, on_click, icon: str = None) -> ft.Button:  # type: ignore[no-untyped-def]
    content = ft.Row(
        controls=[
            ft.Icon(icon, size=18) if icon else None,
            ft.Text(text, size=14, weight=ft.FontWeight.W_500),
        ],
        spacing=8,
        alignment=ft.MainAxisAlignment.CENTER,
    ) if icon else text
    return ft.Button(
        content=content,
        on_click=on_click,
        style=ft.ButtonStyle(
            bgcolor={
                ft.ControlState.DEFAULT: PRIMARY_COLOR,
                ft.ControlState.HOVERED: PRIMARY_DARK,
                ft.ControlState.DISABLED: ft.Colors.GREY_400
            },
            color={ft.ControlState.DEFAULT: ft.Colors.WHITE, ft.ControlState.DISABLED: ft.Colors.WHITE_70},
            shape=ft.RoundedRectangleBorder(radius=20),
            padding=ft.Padding.symmetric(horizontal=20, vertical=16),
        ),
    )


def secondary_button(text: str, on_click, disabled: bool = False, icon: str = None) -> ft.OutlinedButton:  # type: ignore[no-untyped-def]
    content = ft.Row(
        controls=[
            ft.Icon(icon, size=16) if icon else None,
            ft.Text(text, size=13, weight=ft.FontWeight.W_400),
        ],
        spacing=6,
        alignment=ft.MainAxisAlignment.CENTER,
    ) if icon else text
    return ft.OutlinedButton(
        content=content,
        on_click=on_click,
        disabled=disabled,
        style=ft.ButtonStyle(
            color={
                ft.ControlState.DEFAULT: SECONDARY_COLOR,
                ft.ControlState.HOVERED: SECONDARY_DARK,
                ft.ControlState.DISABLED: ft.Colors.GREY_500
            },
            side={
                ft.ControlState.DEFAULT: ft.BorderSide(2, ft.Colors.with_opacity(0.6, SECONDARY_COLOR)),
                ft.ControlState.DISABLED: ft.BorderSide(1, ft.Colors.GREY_400),
            },
            shape=ft.RoundedRectangleBorder(radius=20),
            padding=ft.Padding.symmetric(horizontal=20, vertical=16),
        ),
    )
