import platform
from subprocess import TimeoutExpired as _TimeoutExpired
import shutil
from unittest.mock import Mock, patch

import pytest

from ui.home.ffmpeg_utils import FFmpegUtils, FFmpegVersion, _FFMPEG_MIN_VERSION
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
            with patch("subprocess.run") as run_mock:
                run_mock.return_value.returncode = 0
                run_mock.return_value.stdout = b"ffmpeg version 5.1 Copyright ...\n"
                run_mock.return_value.stderr = b""
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


class TestFFmpegVersion:
    def test_parse_supported_version(self):
        version = FFmpegVersion("ffmpeg version 5.1.2 Copyright ...")
        assert version.major == 5
        assert version.minor == 1
        assert version.patch == 2
        assert version.meets_minimum() is True

    def test_parse_old_version(self):
        version = FFmpegVersion("ffmpeg version 3.4.8 Copyright ...")
        assert version.meets_minimum() is False

    def test_parse_invalid(self):
        version = FFmpegVersion("something else")
        assert version.major == 0
        assert version.meets_minimum() is False

    def test_minimum_version_threshold(self):
        major, minor, patch = _FFMPEG_MIN_VERSION
        version = FFmpegVersion(f"ffmpeg version {major}.{minor}.{patch - 1} ...")
        assert version.meets_minimum() is False


class TestFFmpegDetect:
    @pytest.fixture
    def platform_utils(self):
        return Mock(spec=PlatformUtils)

    @pytest.fixture
    def ffmpeg_utils(self, platform_utils):
        return FFmpegUtils(platform_utils)

    def test_missing_ffmpeg(self, ffmpeg_utils):
        with patch("shutil.which", return_value=None):
            assert ffmpeg_utils.is_ffmpeg_missing() is True
            assert ffmpeg_utils.is_ffmpeg_version_sufficient() is False
            diagnostic = ffmpeg_utils.get_ffmpeg_diagnostic()
            assert "not found in PATH" in diagnostic

    def test_ffmpeg_fails_execution(self, ffmpeg_utils):
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            with patch("subprocess.run", side_effect=OSError("permission denied")):
                assert ffmpeg_utils.is_ffmpeg_missing() is True
                diagnostic = ffmpeg_utils.get_ffmpeg_diagnostic()
                assert "permission denied" in diagnostic

    def test_ffmpeg_nonzero_exit(self, ffmpeg_utils):
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            with patch("subprocess.run") as run_mock:
                run_mock.return_value.returncode = 1
                run_mock.return_value.stdout = b""
                run_mock.return_value.stderr = b"segfault"
                assert ffmpeg_utils.is_ffmpeg_missing() is True
                diagnostic = ffmpeg_utils.get_ffmpeg_diagnostic()
                assert "failed" in diagnostic

    def test_ffmpeg_version_not_ok(self, ffmpeg_utils):
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            with patch("subprocess.run") as run_mock:
                run_mock.return_value.returncode = 0
                run_mock.return_value.stdout = b"not ffmpeg\n"
                run_mock.return_value.stderr = b""
                assert ffmpeg_utils.is_ffmpeg_missing() is True
                diagnostic = ffmpeg_utils.get_ffmpeg_diagnostic()
                assert "failed" in diagnostic

    def test_ffmpeg_valid_old_version(self, ffmpeg_utils):
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            with patch("subprocess.run") as run_mock:
                run_mock.return_value.returncode = 0
                run_mock.return_value.stdout = b"ffmpeg version 3.4.8 Copyright ...\n"
                run_mock.return_value.stderr = b""
                assert ffmpeg_utils.is_ffmpeg_missing() is False
                assert ffmpeg_utils.is_ffmpeg_version_sufficient() is False
                diagnostic = ffmpeg_utils.get_ffmpeg_diagnostic()
                assert f"{'.'.join(str(v) for v in _FFMPEG_MIN_VERSION)}+" in diagnostic

    def test_ffmpeg_valid_new_version(self, ffmpeg_utils):
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            with patch("subprocess.run") as run_mock:
                run_mock.return_value.returncode = 0
                run_mock.return_value.stdout = b"ffmpeg version 5.1.2 Copyright ...\n"
                run_mock.return_value.stderr = b""
                assert ffmpeg_utils.is_ffmpeg_missing() is False
                assert ffmpeg_utils.is_ffmpeg_version_sufficient() is True
                assert ffmpeg_utils.get_ffmpeg_diagnostic() is None

    def test_get_ffmpeg_version_success(self, ffmpeg_utils):
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            with patch("subprocess.run") as run_mock:
                run_mock.return_value.returncode = 0
                run_mock.return_value.stdout = b"ffmpeg version 5.1.2 Copyright ...\n"
                run_mock.return_value.stderr = b""
                assert ffmpeg_utils.get_ffmpeg_version() == "5.1.2"

    def test_get_ffmpeg_version_none_when_missing(self, ffmpeg_utils):
        with patch("shutil.which", return_value=None):
            assert ffmpeg_utils.get_ffmpeg_version() is None

    def test_ffmpeg_timeout(self, ffmpeg_utils):
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            with patch("subprocess.run", side_effect=_TimeoutExpired("/usr/bin/ffmpeg", 5)):
                assert ffmpeg_utils.is_ffmpeg_missing() is True
                diagnostic = ffmpeg_utils.get_ffmpeg_diagnostic()
                assert "timed out" in diagnostic