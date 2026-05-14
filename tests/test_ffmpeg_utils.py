import platform
import shutil
from unittest.mock import Mock, patch

import pytest

from ui.home.ffmpeg_utils import FFmpegUtils
from ui.home.platform_utils import PlatformUtils


class TestFFmpegUtils:
    @pytest.fixture
    def platform_utils(self):
        return Mock(spec=PlatformUtils)

    @pytest.fixture
    def ffmpeg_utils(self, platform_utils):
        return FFmpegUtils(platform_utils)

    def test_is_ffmpeg_missing_true(self, ffmpeg_utils):
        with patch("shutil.which", return_value=None):
            assert ffmpeg_utils.is_ffmpeg_missing() is True

    def test_is_ffmpeg_missing_false(self, ffmpeg_utils):
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            assert ffmpeg_utils.is_ffmpeg_missing() is False

    def test_supports_ffmpeg_auto_install_android(self, platform_utils, ffmpeg_utils):
        platform_utils.is_android_platform.return_value = True
        platform_utils.is_remote_mobile_web_session.return_value = False
        assert ffmpeg_utils.supports_ffmpeg_auto_install() is False

    def test_supports_ffmpeg_auto_install_remote_mobile(self, platform_utils, ffmpeg_utils):
        platform_utils.is_android_platform.return_value = False
        platform_utils.is_remote_mobile_web_session.return_value = True
        assert ffmpeg_utils.supports_ffmpeg_auto_install() is False

    @pytest.mark.parametrize("system", ["linux", "windows", "darwin"])
    def test_supports_ffmpeg_auto_install_supported(self, platform_utils, ffmpeg_utils, system):
        platform_utils.is_android_platform.return_value = False
        platform_utils.is_remote_mobile_web_session.return_value = False
        with patch("platform.system", return_value=system):
            assert ffmpeg_utils.supports_ffmpeg_auto_install() is True

    def test_supports_ffmpeg_auto_install_unsupported(self, platform_utils, ffmpeg_utils):
        platform_utils.is_android_platform.return_value = False
        platform_utils.is_remote_mobile_web_session.return_value = False
        with patch("platform.system", return_value="unknown"):
            assert ffmpeg_utils.supports_ffmpeg_auto_install() is False

    def test_build_ffmpeg_install_hint_android(self, platform_utils, ffmpeg_utils):
        platform_utils.is_android_platform.return_value = True
        hint = ffmpeg_utils.build_ffmpeg_install_hint()
        assert "Android builds should bundle FFmpeg" in hint

    @pytest.mark.parametrize(
        "system,expected",
        [
            ("linux", "Install with your package manager"),
            ("darwin", "Install with Homebrew"),
            ("windows", "Install via Winget"),
            ("unknown", "Install FFmpeg and ensure it is available in PATH"),
        ]
    )
    def test_build_ffmpeg_install_hint_platforms(self, platform_utils, ffmpeg_utils, system, expected):
        platform_utils.is_android_platform.return_value = False
        with patch("platform.system", return_value=system):
            hint = ffmpeg_utils.build_ffmpeg_install_hint()
            assert expected in hint