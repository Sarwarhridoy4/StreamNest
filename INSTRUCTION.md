# Instructions — StreamNest

Comprehensive build, installation, usage, and security instructions for StreamNest, a cross-platform desktop media downloader built with **Flet** and **yt-dlp**.

---

## 1. Installation

### Prerequisites

- **Python 3.11+**
- **FFmpeg** (recommended for video/audio merge, remux, and MP3 extraction)
- **uv** (recommended package manager)

#### Install uv

If `uv` is not installed, install it using one of the following methods:

**Using the official installer (Linux/macOS):**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Using pip:**

```bash
pip install uv
```

**Using Homebrew (macOS):**

```bash
brew install uv
```

After installation, add `uv` to your PATH (the installer prints instructions) and verify:

```bash
uv --version
```

### Step 1 — Clone the repository

```bash
git clone git@github.com:Sarwarhridoy4/StreamNest.git
cd StreamNest
```

### Step 2 — Create and activate a virtual environment

```bash
uv venv
source .venv/bin/activate
```

Windows (PowerShell):

```powershell
uv venv
.venv\Scripts\Activate.ps1
```

### Step 3 — Install dependencies

```bash
uv pip install -e .
```

Optional — install dev/test dependencies:

```bash
uv pip install -e .[test,dev]
```

---

## 2. Run the Application

```bash
python main.py
```

On first launch, StreamNest shows a splash screen, then the Welcome screen. Click **Open StreamNest** to enter the tabbed app UI.

---

## 3. Usage

### Single Download

1. Paste a supported media URL (`http://` or `https://`).
2. Click **Load Formats**.
3. Select mode (video/audio) and quality.
4. Choose save folder (optional).
5. Click **Download**.

### Playlist Download

1. Open the **Playlist** tab.
2. Paste playlist URL.
3. Optional: enter range (`1-5`, `1,3,7-10`).
4. Click **Load Playlist**.
5. Select items.
6. Choose quality and save folder.
7. Click **Download Selected**.

### Welcome and Theme Behavior

1. App starts on the **Welcome** screen.
2. Click **Open StreamNest** to enter the tabbed app UI.
3. Use **Back to Welcome** to return to the welcome screen.
4. Theme follows your system setting by default.
5. Use the floating theme button (top-right) to cycle through System → Dark → Light themes.

---

## 4. FFmpeg Setup

### Automatic install from the app

1. Click **Install FFmpeg** when prompted.
2. Review command preview and confirm.
3. Enter password (Linux privilege flow) when required.
4. Track progress in **FFmpeg Install Log**.

### Manual install

- Linux: `sudo apt install ffmpeg` (or your distribution's package manager)
- macOS: `brew install ffmpeg`
- Windows: install FFmpeg and add it to `PATH` (or use Winget)

Verify:

```bash
ffmpeg -version
```

---

## 5. Build Instructions

### Linux Desktop Executable

```bash
flet build linux
```

Output is located in `build/linux/`.

### Linux Packages (.deb + .AppImage)

See [LINUX_BUILD_INSTRUCTIONS.md](LINUX_BUILD_INSTRUCTIONS.md) for detailed steps.

Brief overview:

```bash
sudo apt update
sudo apt install clang cmake ninja-build pkg-config libgtk-3-dev desktop-file-utils dpkg-dev g++
./scripts/build_linux_packages.sh 2.0.2 amd64
```

### Android APK

1. Set up Java + Android SDK.
2. Switch to the `android` branch.
3. Install dependencies: `uv pip install -e .`
4. Build: `flet build apk`
5. Optional release: `flet build apk --release`

---

## 6. Development

### Testing

```bash
uv pip install -e .[test]
pytest
```

### Linting and Type Checking

```bash
uv pip install -e .[dev]
ruff check .
mypy .
```

### CI

GitHub Actions runs on push/PR to `production`: linting (Ruff), type checking (MyPy), and tests (pytest).

---

## 7. Security

StreamNest implements multiple security layers:

- **URL validation** — blocks `localhost`, `.local`, private/loopback/reserved IPs, embedded credentials, `file://`, `javascript:`, `data:` schemes, and path-traversal fragments. Hostname length capped at 253 chars; dangerous ports rejected.
- **Path traversal protection** — user save directories are validated against allowed roots (home, `$TMPDIR`, `~/Downloads`); escaping paths are redirected to a safe fallback.
- **Download size limit** — capped at 5 GB per file to prevent disk exhaustion.
- **Filename sanitization** — strips reserved characters from path components.
- **Encrypted history** — Fernet-encrypted download history with key file at `0o600` permissions; atomic writes via temp file + `os.replace()`.
- **FFmpeg install hardening** — command binaries allowlisted; passwords validated for length and control characters; all subprocess calls use list form (no `shell=True`).

---

## 8. Project Structure

```
StreamNest/
├── main.py                     # Flet app entry point + splash + bootstrap
├── pyproject.toml              # Project configuration and dependencies
├── uv.lock                     # Locked dependency tree
├── README.md                   # User documentation
├── INSTRUCTION.md              # Build, install, and usage instructions
├── SYSTEM_OVERVIEW.md          # System architecture and design
├── changelog.md                # Release notes
├── LICENSE                     # MIT license
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI
├── scripts/
│   └── build_linux_packages.sh # Linux .deb + .AppImage packaging
├── assets/
│   ├── icon.png                # App logo
│   ├── icon-64/128/256/512.png # Launcher icons
│   ├── demo/                   # Demo video + preview gif
│   └── screenshots/            # UI screenshots
├── services/
│   ├── downloader.py           # yt-dlp threaded wrapper (DownloaderService)
│   └── format_extractor.py     # Metadata + quality extraction (FormatExtractor)
├── state/
│   └── app_state.py            # AppState + HistoryEntry (thread-safe)
├── tests/
│   ├── test_ffmpeg_utils.py
│   └── test_ffmpeg_install_mixin.py
├── ui/
│   ├── components.py           # Reusable UI helpers + theme colors
│   ├── home_view.py            # Compatibility wrapper
│   └── home/
│       ├── home_view.py        # HomeView (mixin composite)
│       ├── control_layout_mixin.py
│       ├── view_layout_mixin.py
│       ├── download_mixin.py
│       ├── playlist_mixin.py
│       ├── history_mixin.py
│       ├── ffmpeg_install_mixin.py
│       ├── ffmpeg_utils.py     # FFmpegUtils + FFmpegVersion
│       ├── platform_utils.py   # PlatformUtils
│       └── theme_manager.py    # ThemeManager
└── utils/
    ├── file_manager.py         # Path/size/speed/eta helpers + path traversal protection
    ├── history_store.py        # Fernet-encrypted history persistence
    └── validators.py           # URL validation + filename sanitization
```

---

## 9. Developer Contacts

- **Author:** Sarwar Hossain
- **GitHub:** [Sarwarhridoy4](https://github.com/Sarwarhridoy4)
- **Website:** [streamnest-puce.vercel.app](https://streamnest-puce.vercel.app)
- **License:** MIT

---

**Disclaimer:** Use this software lawfully and in compliance with platform terms, copyright, and local regulations.
