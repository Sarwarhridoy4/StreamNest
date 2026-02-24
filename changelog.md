# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added
- Welcome screen flow with one-click entry into tabbed app UI.
- Bottom navigation tabs for Single, Playlist, and About sections.
- Dedicated History tab with professional list layout and detailed modal view per download entry.
- Encrypted persistent download history storage using Fernet (`state/download_history.enc`).
- Erase History action with confirmation dialog.
- FFmpeg auto-install action from UI with OS-specific command planning (Linux/macOS/Windows).
- FFmpeg installer confirmation/password dialogs and live install log window.
- `yt-dlp` runtime log collection with in-app log viewer.
- Manual FFmpeg re-check action in the UI.
- Modular `ui/home/` package split with mixins for layout, downloads, playlist, history, and FFmpeg flows.

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
