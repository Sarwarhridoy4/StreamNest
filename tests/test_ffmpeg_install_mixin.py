from unittest.mock import Mock, patch

import pytest

from ui.home.ffmpeg_install_mixin import FfmpegInstallMixin


class MockFfmpegInstallMixin(FfmpegInstallMixin):
    def __init__(self, ffmpeg_utils):
        self.ffmpeg_utils = ffmpeg_utils
        self.ffmpeg_missing = None
        self.ffmpeg_install_hint = None
        self.ffmpeg_install_supported = True
        # Mock UI elements with value and visible attributes
        self.ffmpeg_warning_text = Mock()
        self.ffmpeg_warning_text.value = ""
        self.ffmpeg_warning_text.visible = False
        self.welcome_ffmpeg_warning_text = Mock()
        self.welcome_ffmpeg_warning_text.value = ""
        self.welcome_ffmpeg_warning_text.visible = False
        self.install_ffmpeg_btn = Mock()
        self.install_ffmpeg_btn.visible = False
        self.welcome_install_ffmpeg_btn = Mock()
        self.welcome_install_ffmpeg_btn.visible = False

    def _set_status(self, status):
        pass

    def _show_popup(self, message, color):
        pass


class TestFfmpegInstallMixin:
    @pytest.fixture
    def ffmpeg_utils(self):
        return Mock()

    @pytest.fixture
    def mixin(self, ffmpeg_utils):
        return MockFfmpegInstallMixin(ffmpeg_utils)

    def test_is_ffmpeg_missing_wrapper_success(self, mixin, ffmpeg_utils):
        ffmpeg_utils.is_ffmpeg_missing.return_value = False
        assert mixin._is_ffmpeg_missing() is False
        ffmpeg_utils.is_ffmpeg_missing.assert_called_once()

    def test_is_ffmpeg_missing_wrapper_exception(self, mixin, ffmpeg_utils):
        ffmpeg_utils.is_ffmpeg_missing.side_effect = Exception("test")
        assert mixin._is_ffmpeg_missing() is True

    def test_build_ffmpeg_install_hint_wrapper_success(self, mixin, ffmpeg_utils):
        ffmpeg_utils.build_ffmpeg_install_hint.return_value = "Install hint"
        assert mixin._build_ffmpeg_install_hint() == "Install hint"
        ffmpeg_utils.build_ffmpeg_install_hint.assert_called_once()

    def test_build_ffmpeg_install_hint_wrapper_exception(self, mixin, ffmpeg_utils):
        ffmpeg_utils.build_ffmpeg_install_hint.side_effect = Exception("test")
        assert mixin._build_ffmpeg_install_hint() == "FFmpeg not found."

    def test_on_recheck_ffmpeg_with_wrappers(self, mixin, ffmpeg_utils):
        mixin.ffmpeg_missing = True
        mixin.ffmpeg_install_hint = "old hint"
        ffmpeg_utils.is_ffmpeg_missing.return_value = False
        ffmpeg_utils.build_ffmpeg_install_hint.return_value = "Install hint"
        ffmpeg_utils.get_ffmpeg_version.return_value = "5.1.2"

        mixin._on_recheck_ffmpeg(None)

        assert mixin.ffmpeg_missing is False
        assert mixin.ffmpeg_install_hint == "FFmpeg 5.1.2 detected."
        assert mixin.ffmpeg_warning_text.value == "FFmpeg 5.1.2 detected."
        assert mixin.ffmpeg_warning_text.visible is False
        assert mixin.welcome_ffmpeg_warning_text.value == "FFmpeg 5.1.2 detected."
        assert mixin.welcome_ffmpeg_warning_text.visible is False
        assert mixin.install_ffmpeg_btn.visible is False
        assert mixin.welcome_install_ffmpeg_btn.visible is False

    def test_on_recheck_ffmpeg_fallback(self, mixin, ffmpeg_utils):
        # Mock the AttributeError for wrappers
        with patch.object(mixin, '_is_ffmpeg_missing', side_effect=AttributeError):
            with patch.object(mixin, '_build_ffmpeg_install_hint', side_effect=AttributeError):
                ffmpeg_utils.is_ffmpeg_missing.return_value = True
                ffmpeg_utils.build_ffmpeg_install_hint.return_value = "fallback hint"

                mixin._on_recheck_ffmpeg(None)

                assert mixin.ffmpeg_missing is True
                assert mixin.ffmpeg_install_hint == "fallback hint"