from __future__ import annotations

import flet as ft


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
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
    )


def primary_button(text: str, on_click) -> ft.ElevatedButton:  # type: ignore[no-untyped-def]
    return ft.ElevatedButton(content=text, on_click=on_click)


def secondary_button(text: str, on_click, disabled: bool = False) -> ft.OutlinedButton:  # type: ignore[no-untyped-def]
    return ft.OutlinedButton(content=text, on_click=on_click, disabled=disabled)
