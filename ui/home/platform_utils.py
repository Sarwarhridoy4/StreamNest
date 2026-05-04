from __future__ import annotations

import platform
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import flet as ft

__all__ = ["PlatformUtils"]


class PlatformUtils:
    """Utility class for platform detection and capability checking."""

    def __init__(self, page: ft.Page) -> None:
        """Initialize platform utilities with the Flet page."""
        self.page = page
        self.platform_name = self._get_platform_name()

    def _get_platform_name(self) -> str:
        """Get the normalized platform name from the Flet page."""
        return str(getattr(self.page, "platform", "")).lower()

    def is_mobile_platform(self) -> bool:
        """Check if the current platform is a mobile platform (Android or iOS)."""
        return "android" in self.platform_name or "ios" in self.platform_name

    def is_android_platform(self) -> bool:
        """Check if the current platform is Android."""
        return "android" in self.platform_name

    def is_remote_mobile_web_session(self) -> bool:
        """Check if this is a remote mobile web session (e.g., Android accessing via web)."""
        return self.is_mobile_platform() and bool(getattr(self.page, "web", False))

    def supports_directory_picker(self) -> bool:
        """Check if the current platform supports directory picker functionality."""
        if "ios" in self.platform_name:
            return False
        return not self.is_remote_mobile_web_session()

    def supports_open_folder(self) -> bool:
        """Check if the current platform supports opening folders in the system file manager."""
        system = platform.system().lower()
        return system.startswith("windows") or system == "darwin" or system.startswith("linux")