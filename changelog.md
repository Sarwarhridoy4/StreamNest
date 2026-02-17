# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added
- Welcome screen flow with one-click entry into tabbed app UI.
- Bottom navigation tabs for Single, Playlist, and About sections.
- Dedicated History tab with professional list layout and detailed modal view per download entry.
- Encrypted persistent download history storage using Fernet (`state/download_history.enc`).
- Erase History action with confirmation dialog.

### Changed
- Welcome screen card layout updated to keep the rounded welcome box centered.
- Improved URL validation to block local/private network targets.
- Safer output naming for downloads with restricted filenames.
- Added filename length and platform-safe filename enforcement to avoid failures on long/unsupported video titles.
- Startup error screen now avoids exposing full traceback details in the UI.
- History entries now include structured metadata (platform, mode, quality, URL, timestamp, save folder, result).
