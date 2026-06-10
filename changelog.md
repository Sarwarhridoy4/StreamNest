# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added
- FFmpeg version display in the UI on startup and re-check.
- Robust `ffmpeg -version` detection with timeout, error classification, and minimum version check.
- FFmpeg minimum version threshold (`4.0.0`) enforced during detection.
- FFmpeg diagnostic API exposing human-readable failure reasons (not in PATH, crash, timeout, old version).
- `is_ffmpeg_version_sufficient()` and `get_ffmpeg_version()` helpers in `FFmpegUtils`.

### Changed
- FFmpeg warning text is always visible; uses green text when detected and red text when missing.
- FFmpeg installer and re-check paths show `FFmpeg {version} detected.` when present.
- `FFmpeg::is_ffmpeg_missing()` now validates actual `ffmpeg -version` execution instead of only `shutil.which`.
- `DownloaderService._detect_ffmpeg_dir()` now runs `ffmpeg -version` before accepting a binary directory.
- FFmpeg re-check flow prefers version display over generic install hint when FFmpeg is found.

### Fixed
- Flet splash-screen `RuntimeError` caused by updating a control before it was attached to the page.
- Startup task argument mismatch (`initialize_app_async`) after refactor.
- FFmpeg installation completion now toggles warning text color and visibility correctly.

## [2.0.1] - 2026-06-10

### Added
- Welcome screen flow with one-click entry into tabbed app UI.
- Bottom navigation tabs for Single, Playlist, History, and About sections.
- Dedicated History tab with professional list layout and detailed modal view per download entry.
- Encrypted persistent download history storage using Fernet (`state/download_history.enc`).
- Erase History action with confirmation dialog.
- FFmpeg auto-install action from UI with OS-specific command planning (Linux/macOS/Windows).
- FFmpeg installer confirmation/password dialogs and live install log window.
- `yt-dlp` runtime log collection with in-app log viewer.
- Manual FFmpeg re-check action in the UI.
- Modular `ui/home/` package split with mixins for layout, downloads, playlist, history, and FFmpeg flows.
- Modern professional UI design with indigo/purple color scheme, subtle gradients, enhanced shadows, and icons on buttons.
- Improved typography with better font weights and sizes for enhanced readability.
- Floating theme toggle button accessible from all screens (cycles through System → Dark → Light themes).

### Changed
- About tab now includes the official StreamNest website link (`https://streamnest-puce.vercel.app`).
- Welcome screen card layout updated to keep the rounded welcome box centered.
- Improved URL validation to block local/private network targets.
- Safer output naming for downloads with restricted filenames.
- Added filename length and platform-safe filename enforcement to avoid failures on long/unsupported video titles.
- Startup error screen now avoids exposing full traceback details in the UI.
- History entries now include structured metadata (platform, mode, quality, URL, timestamp, save folder, result).
- `ui/home_view.py` now acts as a compatibility wrapper that re-exports `HomeView` from `ui/home/home_view.py`.
- README screenshots section now enumerates all available images.
- Linux packaging script now installs apt dependencies one-by-one and auto-installs `appimagetool` from AppImageKit releases when apt does not provide it.
- Linux packaging dependency checks now try both `lld-20` and `lld` to improve compatibility across Ubuntu/Debian variants.
- Linux packaging now installs a concrete `libstdc++-XX-dev` package when needed and auto-installs `lld-20` if `/usr/lib/llvm-20/bin` lacks a linker.
- Linux packaging stages CMake installs under `build/` to avoid requiring root access to `/usr/local`.
- Flet app metadata version now uses valid semver (`2.0.0`) for packaging tools.
- Launcher icon generation uses a non-empty PNG asset to avoid `flutter_launcher_icons` failures.

## [2.0.0] - 2026-06-10

### Added
- Initial public release.
- Core download engine wrapping `yt-dlp` with threaded execution, progress hooks, and cancel support.
- Single-video and playlist download modes with quality selection.
- Audio extraction to MP3 via FFmpeg.
- Persisted download history and state using encrypted storage.
- FFmpeg presence auto-detection and guided installer on first launch.
- About / Developer info screen.
- Dark and light theme support with system-aware defaults.
- Linux `.deb` and `.AppImage` packaging scripts.
