from __future__ import annotations

import platform
import re
import shutil
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .platform_utils import PlatformUtils

__all__ = ["FFmpegUtils"]

_FFMPEG_OK_SENTINEL = "ffmpeg version"
_FFMPEG_MIN_VERSION = (4, 0, 0)


class FFmpegVersion:
    """Parsed FFmpeg version string."""

    def __init__(self, raw: str) -> None:
        self.raw = raw
        self.major = 0
        self.minor = 0
        self.patch = 0
        self._parse(raw)

    def _parse(self, raw: str) -> None:
        match = re.search(r"ffmpeg\s+version\s+([0-9]+(?:\.[0-9]+)+)", raw, re.IGNORECASE)
        if not match:
            return
        parts = [int(p) for p in match.group(1).split(".")[:3]]
        while len(parts) < 3:
            parts.append(0)
        self.major, self.minor, self.patch = parts

    def meets_minimum(self) -> bool:
        current = (self.major, self.minor, self.patch)
        return current >= _FFMPEG_MIN_VERSION

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


class _FFmpegDetectedInfo:
    """Aggregated detection results for FFmpeg on the system."""

    def __init__(self) -> None:
        self.found = False
        self.bin_path: str | None = None
        self.version: FFmpegVersion | None = None
        self.diagnostic: str | None = None


class FFmpegUtils:
    """Utility class for FFmpeg detection and installation guidance."""

    def __init__(self, platform_utils: PlatformUtils) -> None:
        """Initialize FFmpeg utilities with platform information."""
        self.platform_utils = platform_utils

    def _run_ffmpeg_version_command(self, timeout: int = 5) -> tuple[str, str, int]:
        """Run ``ffmpeg -version`` and return ``(stdout, stderr, returncode)``."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                timeout=timeout,
            )
            stdout_value = result.stdout.decode("utf-8", "replace")
            stderr_value = result.stderr.decode("utf-8", "replace")
            return stdout_value, stderr_value, result.returncode
        except FileNotFoundError:
            return "", "ffmpeg executable not found", -1
        except OSError as exc:
            return "", str(exc), -1
        except subprocess.TimeoutExpired as exc:
            return "", f"ffmpeg -version timed out after {timeout}s", -1

    def _parse_ffmpeg_version(self, stdout: str) -> FFmpegVersion | None:
        """Parse the first line of ``ffmpeg -version`` output into a version object."""
        first_line = stdout.splitlines()[0] if stdout else ""
        if not first_line:
            return None
        if _FFMPEG_OK_SENTINEL.casefold() not in first_line.casefold():
            return None
        return FFmpegVersion(first_line)

    def _detect_ffmpeg(self, timeout: int = 5) -> _FFmpegDetectedInfo:
        """Run ``ffmpeg -version`` and return structured detection results."""
        info = _FFmpegDetectedInfo()
        ffmpeg_bin = shutil.which("ffmpeg")
        if not ffmpeg_bin:
            info.diagnostic = "ffmpeg not found in PATH"
            return info
        info.found = True
        info.bin_path = str(ffmpeg_bin)
        stdout, stderr, rc = self._run_ffmpeg_version_command(timeout=timeout)
        if rc != 0 or _FFMPEG_OK_SENTINEL.casefold() not in stdout.casefold():
            info.diagnostic = f"ffmpeg at {ffmpeg_bin} failed: "
            info.diagnostic += (stderr or stdout or "unknown error").strip().splitlines()[0]
            info.found = False
            return info
        info.found = True
        info.version = self._parse_ffmpeg_version(stdout)
        return info

    def is_ffmpeg_missing(self) -> bool:
        """Check if FFmpeg is installed, callable, and returns a valid version string."""
        return not self._detect_ffmpeg().found

    def is_ffmpeg_version_sufficient(self) -> bool:
        """Return ``True`` when FFmpeg is detected and meets the minimum version."""
        info = self._detect_ffmpeg()
        return info.found and info.version is not None and info.version.meets_minimum()

    def get_ffmpeg_version(self) -> str | None:
        """Return the detected FFmpeg version string, or ``None`` if unavailable."""
        info = self._detect_ffmpeg()
        return str(info.version) if info.version is not None else None

    def get_ffmpeg_diagnostic(self) -> str | None:
        """Return a human-readable diagnostic string if FFmpeg is not usable."""
        info = self._detect_ffmpeg()
        if info.found:
            if info.version is None:
                return f"FFmpeg detected at {info.bin_path}, but version could not be parsed."
            if not info.version.meets_minimum():
                return f"FFmpeg {info.version} is installed, but version {'.'.join(str(v) for v in _FFMPEG_MIN_VERSION)}+ is required."
            return None
        return info.diagnostic or "FFmpeg is not available."

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