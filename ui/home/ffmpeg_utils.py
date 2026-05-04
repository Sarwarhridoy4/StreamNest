from __future__ import annotations

import platform
import shutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .platform_utils import PlatformUtils

__all__ = ["FFmpegUtils"]


class FFmpegUtils:
    """Utility class for FFmpeg detection and installation guidance."""

    def __init__(self, platform_utils: PlatformUtils) -> None:
        """Initialize FFmpeg utilities with platform information."""
        self.platform_utils = platform_utils

    def is_ffmpeg_missing(self) -> bool:
        """Check if FFmpeg is installed and available in the system PATH."""
        return shutil.which("ffmpeg") is None

    def supports_ffmpeg_auto_install(self) -> bool:
        """Check if the current platform supports automatic FFmpeg installation."""
        if self.platform_utils.is_android_platform() or self.platform_utils.is_remote_mobile_web_session():
            return False
        system = platform.system().lower()
        return system.startswith("linux") or system.startswith("windows") or system == "darwin"

    def build_ffmpeg_install_hint(self) -> str:
        """Build a platform-specific hint message for FFmpeg installation."""
        if self.platform_utils.is_android_platform():
            return "FFmpeg not found. Android builds should bundle FFmpeg or use media that does not require post-processing."

        system = platform.system().lower()
        base_message = "FFmpeg not found."

        return self._get_platform_specific_install_hint(system, base_message)

    def _get_platform_specific_install_hint(self, system: str, base_message: str) -> str:
        """Get platform-specific FFmpeg installation instructions."""
        if system.startswith("linux"):
            return f"{base_message} Install with your package manager, e.g. `sudo apt install ffmpeg`."
        elif system == "darwin":
            return f"{base_message} Install with Homebrew: `brew install ffmpeg`."
        elif system.startswith("windows"):
            return f"{base_message} Install via Winget: `winget install Gyan.FFmpeg`."
        elif system == "android":
            return f"{base_message} Bundle FFmpeg with the app or include a mobile FFmpeg integration."
        else:
            return f"{base_message} Install FFmpeg and ensure it is available in PATH."