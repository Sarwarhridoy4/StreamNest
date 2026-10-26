# AGENTS.md — StreamNest Project Instructions

## Project overview

**StreamNest** is a cross-platform desktop media downloader built with **Flet** (Python GUI) and **yt-dlp** (download engine). It supports single-media and playlist downloads, quality selection, audio (MP3) extraction via FFmpeg, playlist range/item selection, live progress + speed + ETA, FFmpeg auto-install, encrypted download history, and System/Dark/Light themes.

**Author:** Sarwar Hossain (Sarwarhridoy4)
**Repo:** https://github.com/Sarwarhridoy4/StreamNest
**Current version:** 2.0.3
**Python:** 3.11+

---

## Repository layout

```
StreamNest/
├── main.py                     # Flet entry point + splash screen + app bootstrap
├── pyproject.toml              # Project config, deps, ruff/mypy/flet settings
├── uv.lock                     # Locked dependency tree
├── README.md                   # User documentation
├── SYSTEM_OVERVIEW.md          # Full architecture + data-flow diagrams
├── INSTRUCTION.md              # Build/install/usage/security instructions
├── AGENTS.md                   # This file (agent operating instructions)
├── changelog.md                # Release notes
├── features.md                 # yt-dlp-aligned feature improvement proposals (+status)
├── LICENSE                     # MIT
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI (ruff, mypy, pytest)
├── scripts/
│   └── build_linux_packages.sh # Linux .deb + .AppImage packaging
├── assets/                     # Icons, demo media, screenshots
├── services/
│   ├── downloader.py           # DownloaderService: threaded yt-dlp wrapper (DownloadRequest/ProgressInfo/DownloadResult)
│   └── format_extractor.py     # FormatExtractor: metadata + quality extraction (MediaInfo/PlaylistInfo/QualityOption)
├── state/
│   └── app_state.py            # AppState (thread-safe shared state) + HistoryEntry dataclass
├── tests/
│   ├── __init__.py
│   ├── test_ffmpeg_utils.py
│   └── test_ffmpeg_install_mixin.py
├── ui/
│   ├── components.py           # Reusable UI primitives + indigo theme colors
│   ├── home_view.py            # Compatibility wrapper re-exporting HomeView
│   └── home/
│       ├── __init__.py
│       ├── home_view.py        # HomeView mixin composite + all event handlers
│       ├── control_layout_mixin.py   # Form controls + button wiring
│       ├── view_layout_mixin.py      # Panels, tabs, navigation host
│       ├── download_mixin.py         # Download start/cancel/progress/result handlers
│       ├── playlist_mixin.py         # Playlist load/item-select/download orchestration
│       ├── history_mixin.py          # History rendering + erase flow
│       ├── ffmpeg_install_mixin.py   # FFmpeg detect/install/re-check UI flow
│       ├── ffmpeg_utils.py           # FFmpeg detection, version, diagnostics, install hints
│       ├── platform_utils.py         # Platform detection + capability checks
│       └── theme_manager.py          # ThemeManager: palette + brightness listener
└── utils/
    ├── file_manager.py         # Path/size/speed/eta helpers + path traversal protection
    ├── history_store.py        # Fernet-encrypted history persistence (XDG state dir)
    └── validators.py           # URL safety validation + filename sanitization
```

---

## Architecture (layered, mixin-based)

```
main.py  →  HomeView (mixin composite)
├─ control_layout_mixin.py   # form/button controls
├─ view_layout_mixin.py      # panels + bottom nav tabs
├─ download_mixin.py         # download orchestration (calls DownloaderService)
├─ playlist_mixin.py         # playlist load/select/download
├─ history_mixin.py          # history UI
├─ ffmpeg_install_mixin.py   # FFmpeg detect/install UI
├─ theme_manager.py          # theme palette + platform brightness listener
├─ platform_utils.py         # platform/capability checks
└─ ffmpeg_utils.py           # FFmpeg detection/diagnostics/install hints

services/
├─ downloader.py   # threaded yt-dlp wrapper (start_download/cancel/is_busy/_build_options)
└─ format_extractor.py # yt-dlp extract_info calls; resolve_format_selector; normalize_playlist_range

state/
└─ app_state.py    # thread-safe AppState (Lock) + HistoryEntry (to_dict/from_dict)

utils/
├─ file_manager.py   # resolve_download_directory, format_bytes/speed/eta, path traversal guard
├─ history_store.py  # Fernet-encrypted history (XDG state dir + TMPDIR fallback, key 0o600)
└─ validators.py     # is_valid_url (HTTP(S) only, no localhost/private IPs/credentials), sanitize_filename_component
```

**Key principles:**
- Separation of concerns: UI (Flet), services (yt-dlp), state (dataclasses + Lock), utils (file/history/validation).
- Thread safety: `AppState` uses `threading.Lock`; `DownloaderService` runs yt-dlp in a daemon thread with a cancel `Event` and active-download lock.
- Mixin composition: `HomeView` composes behavior via mixins.
- Defensive URL validation: rejects localhost, `.local`, private/loopback/reserved IPs, embedded credentials, dangerous schemes.

---

## How to run / develop

### Prerequisites
- Python 3.11+
- FFmpeg (recommended for merge/remux/extract)
- uv (recommended package manager)

### Install
```bash
uv venv
source .venv/bin/activate          # Linux/macOS
# Windows: .venv\Scripts\Activate.ps1
uv pip install -e .
```

### Run the app
```bash
python main.py
```

### Install dev/test deps
```bash
uv pip install -e .[test,dev]
```

### Lint (Ruff)
```bash
ruff check .
```

### Type check (MyPy)
```bash
mypy .
```

### Tests
```bash
pytest
```

### Build Linux packages (.deb + .AppImage)
```bash
./scripts/build_linux_packages.sh 2.0.3 amd64
```
Prerequisites: `clang cmake ninja-build pkg-config libgtk-3-dev desktop-file-utils dpkg-dev g++ lld-20`

### Build Android APK (on `android` branch)
```bash
uv pip install -e .
flet build apk
```

---

## Coding conventions

- **No comments unless asked** (per project instruction).
- **Type hints required:** `disallow_untyped_defs = true` in mypy; use `from __future__ import annotations`.
- **Ruff line-length:** 140, target py311.
- **Flet Dropdown** uses `on_select` (not `on_change`).
- **Dataclasses** for request/result/info objects (`DownloadRequest`, `ProgressInfo`, `DownloadResult`, `QualityOption`, `MediaInfo`, `PlaylistEntry`, `PlaylistInfo`, `HistoryEntry`).
- **Mixins** for UI concerns; each mixin owns a slice of `HomeView` behavior.
- **State** flows through `AppState` (thread-safe); UI callbacks update state then call `_refresh_view()` / `_page_update()`.
- **Download flow:** `DownloadMixin._on_download` → `DownloaderService.start_download` → yt-dlp thread → progress hooks → UI callbacks.
- **Security:** never log secrets; `subprocess` calls use list form (no `shell=True`); save directories validated against allowed roots (home, `$TMPDIR`, `~/Downloads`).

---

## Recent work (this session)

1. **`features.md`** — yt-dlp-aligned feature improvement proposal across 9 categories. Each item marked ✅ Implemented or ⬜ Pending.

2. **`feature/subtitles` branch** — Subtitles write/embed:
   - `services/downloader.py`: `DownloadRequest` gains `subtitles`, `embed_subtitles`, `subtitles_langs`, `convert_subs`; `_build_options` sets `writesubtitles`/`subtitleslangs`/`convertsubs` and appends `FFmpegEmbedSubtitle` postprocessor.
   - `state/app_state.py`, `ui/home/*`: matching state + UI controls wired into single & playlist downloads.

3. **`feature/thumbnails` branch** — Thumbnail write/embed:
   - `services/downloader.py`: `DownloadRequest` gains `thumbnails`, `embed_thumbnail`, `convert_thumbnails`; `_build_options` sets `writethumbnail`/`convertthumbnails` and appends `FFmpegEmbedThumbnail` postprocessor (video + audio).
   - `state/app_state.py`, `ui/home/*`: matching state + UI controls wired into single & playlist downloads.
   - `pyproject.toml`, `scripts/build_linux_packages.sh`: version `2.0.2` → `2.0.3`.
   - `changelog.md`: subtitle + thumbnail entries under [Unreleased].

4. **`feature/playlist` branch** — Playlist start/end/skip-unavailable/no-abort-on-error:
   - `services/downloader.py`: `DownloadRequest` gains `playlist_start`, `playlist_end`, `skip_unavailable`, `no_abort_on_error`; `_build_options` sets `playliststart`/`playlistend`/`skipunavailable`/`noabortonerror` (with `ignoreerrors`).
   - `state/app_state.py`: matching state fields.
   - `ui/home/control_layout_mixin.py`: start/end text fields, skip-unavailable/no-abort checkboxes.
   - `ui/home/download_mixin.py`: `_on_playlist_options_change` handler + `_parse_positive_int` helper.
   - `ui/home/playlist_mixin.py`: playlist download request wiring + start<=end validation.
   - `ui/home/view_layout_mixin.py`: "Playlist options" section in playlist card.

5. **`feature/cookies-proxy` branch** — Cookies from browser/file + proxy:
   - `services/downloader.py`: `DownloadRequest` gains `cookies_from_browser`, `cookies_file`, `proxy`; `_build_options` sets `cookiesfrombrowser`/`cookies`/`proxy`.
   - `state/app_state.py`: matching state fields.
   - `ui/home/control_layout_mixin.py`: browser dropdown, cookies file field, proxy field.
   - `ui/home/download_mixin.py`: `_on_cookies_proxy_change` handler.
   - `ui/home/playlist_mixin.py`: playlist download request wiring.
   - `ui/home/view_layout_mixin.py`: "Cookies / Proxy" section in left panel.
   - `ui/home/home_view.py`: cookie/proxy state initialization.

6. **AGENTS.md** — this file (project operating instructions).

---

## Git workflow

- Default branch: `production`
- Feature work: create a new branch from the **current workbranch** (e.g. `feature/cookies-proxy` → `feature/rate-limit`) rather than switching back to `production` and branching from there. Branching from production after local feature work has diverged can cause merge conflicts; branching from the current workbranch keeps history linear and avoids conflict resolution.
- Commit and push feature branches; open PRs against `production`
- Do NOT commit unless explicitly asked by the user

---

## Next features from features.md (in suggested order)

1. ✅ Subtitles write/embed — DONE (`feature/subtitles`)
2. ✅ Thumbnails write/embed — DONE (`feature/thumbnails`)
3. ✅ Playlist start/end/skip-unavailable/no-abort-on-error — DONE (`feature/playlist`)
4. ✅ Cookies from browser/file + proxy — DONE (`feature/cookies-proxy`)
5. ⬜ Rate limit + sleep interval
6. ⬜ Download archive + queue
7. ⬜ yt-dlp self-update/version + format sort

When implementing a new feature, follow the same pattern as subtitles/thumbnails/playlist/cookies-proxy:
1. Add fields to `DownloadRequest` in `services/downloader.py`
2. Wire yt-dlp options + postprocessors in `_build_options`
3. Add matching state fields to `state/app_state.py`
4. Add UI controls to `ui/home/control_layout_mixin.py` (use `on_select` for Dropdown, `on_change` for Checkbox/TextField)
5. Add change handler to `ui/home/download_mixin.py` + wire into single and playlist `DownloadRequest`
6. Add section to `ui/home/view_layout_mixin.py` relevant panel
7. Initialize state in `ui/home/home_view.py` (via `AppState` defaults)
8. Mark feature as ✅ Implemented in `features.md`
9. Compile-check: `.venv/bin/python -m py_compile <files>`
10. Lint: `ruff check .` | Type check: `mypy .`
11. Commit to a feature branch and push
