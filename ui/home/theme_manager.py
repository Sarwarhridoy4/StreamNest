from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from ui.components import PRIMARY_COLOR

if TYPE_CHECKING:
    from .home_view import HomeView

__all__ = ["ThemeManager"]


class ThemeManager:
    """Manager class for theme-related functionality and styling."""

    def __init__(self, home_view: HomeView) -> None:
        """Initialize theme manager with reference to the home view."""
        self.home_view = home_view
        self._platform_theme_listener_enabled = False

    def setup_theme_listener(self) -> None:
        """Setup platform brightness change listener for theme updates."""
        try:
            self.home_view.page.on_platform_brightness_change = self.home_view._on_platform_brightness_change
            self._platform_theme_listener_enabled = True
        except Exception:
            self._platform_theme_listener_enabled = False

    def is_theme_dark(self) -> bool:
        """Determine if the current theme is dark mode."""
        if self.home_view.page.theme_mode == ft.ThemeMode.DARK:
            return True
        if self.home_view.page.theme_mode == ft.ThemeMode.LIGHT:
            return False
        return self._device_prefers_dark()

    def _device_prefers_dark(self) -> bool:
        """Check if the device prefers dark mode based on platform brightness."""
        brightness = getattr(self.home_view.page, "platform_brightness", None)
        if brightness is None:
            return False
        brightness_enum = getattr(ft, "Brightness", None)
        if brightness_enum is not None and brightness == brightness_enum.DARK:
            return True
        if isinstance(brightness, str):
            return brightness.lower() == "dark"
        return False

    def apply_theme_palette(self) -> None:
        """Apply the current theme colors to all UI components."""
        is_dark = self.is_theme_dark()
        self.home_view.page.bgcolor = "#0B0B0D" if is_dark else "#FFF7F5"

        # Update progress bars
        self.home_view.progress_bar.bgcolor = PRIMARY_COLOR
        self.home_view.playlist_progress_bar.bgcolor = PRIMARY_COLOR

        # Update card backgrounds
        self._apply_card_backgrounds(is_dark)
        self._apply_input_styles(is_dark)

    def _apply_card_backgrounds(self, is_dark: bool) -> None:
        """Apply background colors to all cards based on theme."""
        card_bg = "#16161A" if is_dark else "#FFFFFF"

        cards = [
            "left_panel", "right_panel", "welcome_card",
            "playlist_card", "history_card", "about_card"
        ]

        for card_name in cards:
            if hasattr(self.home_view, card_name):
                card = getattr(self.home_view, card_name)
                card.bgcolor = card_bg

    def _apply_input_styles(self, is_dark: bool) -> None:
        """Apply consistent styling to input fields and dropdowns."""
        fill_color = "#202020" if is_dark else "#FFFFFF"
        border_color = ft.Colors.with_opacity(0.35, PRIMARY_COLOR)
        focused_border_color = PRIMARY_COLOR

        inputs = [
            self.home_view.url_field,
            self.home_view.playlist_url_field,
            self.home_view.playlist_range_field,
        ]
        dropdowns = [
            self.home_view.quality_dropdown,
            self.home_view.playlist_quality_dropdown,
        ]

        # Style input fields
        for control in inputs:
            control.filled = True
            control.fill_color = fill_color
            control.border_radius = 14
            control.content_padding = ft.Padding.symmetric(horizontal=14, vertical=12)
            control.border_color = border_color
            control.focused_border_color = focused_border_color
            control.focused_border_width = 2

        # Style dropdowns
        for control in dropdowns:
            control.filled = True
            control.fill_color = fill_color
            control.border_radius = 14
            control.content_padding = ft.Padding.symmetric(horizontal=14, vertical=12)
            control.border_color = border_color
            control.focused_border_color = focused_border_color
            control.focused_border_width = 2