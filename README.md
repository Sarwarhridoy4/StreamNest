# StreamNest

A desktop YouTube downloader built with **Flet** and **yt-dlp**.

StreamNest provides a clean UI for:
- single video/audio downloads
- dynamic format loading
- playlist loading with range support and item selection
- live progress updates (progress, speed, ETA)

## Features

- Dynamic format loading (`Load Formats`) before download
- Single download modes:
  - `Video (MP4)`
  - `Audio (MP3)`
- Dedicated playlist window:
  - playlist URL input
  - range input (examples: `1-5`, `1,3,7-10`)
  - selectable playlist item list
  - playlist-specific quality selector
  - playlist-specific save folder
- Separate progress UX:
  - single download progress on main screen
  - playlist download progress inside playlist window
- Folder actions:
  - choose save folder
  - open selected folder directly
- FFmpeg-aware post-processing hooks
- Download history panel
- Mobile-responsive layout within Flet window

## Tech Stack

- Python 3.11+
- [Flet](https://flet.dev/)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- FFmpeg (recommended/required for best post-processing)

## Project Structure

```text
StreamNest/
├── main.py
├── requirements.txt
├── services/
│   ├── downloader.py
│   └── format_extractor.py
├── state/
│   └── app_state.py
├── ui/
│   ├── components.py
│   └── home_view.py
└── utils/
    ├── file_manager.py
    └── validators.py
```

## Setup

1. Clone the repository and open the project folder.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## FFmpeg Setup

FFmpeg is strongly recommended.

- **Linux**: install via your package manager (`ffmpeg` package)
- **macOS**: `brew install ffmpeg`
- **Windows**: install FFmpeg and add it to `PATH`

Verify:

```bash
ffmpeg -version
```

## Run

```bash
python main.py
```

## Usage

### Single Video/Audio

1. Paste a YouTube URL.
2. Click **Load Formats**.
3. Choose mode (`Video` or `Audio`) and quality.
4. Select save folder (optional: **Open Folder**).
5. Click **Download**.

### Playlist

1. Click **Open Playlist Window**.
2. Paste playlist URL.
3. Optional: enter range (`1-5`, `1,3,7-10`).
4. Click **Load Playlist**.
5. Select items to download.
6. Choose quality and save folder.
7. Click **Download Selected**.

## Notes

- Only YouTube URLs are accepted.
- Live speed/ETA depend on metrics provided by source/yt-dlp; fallback estimations are used when possible.
- FFmpeg improves merge/remux/post-processing behavior and quality.

## Troubleshooting

### UI opens but actions do nothing
- Ensure dependencies are installed in the active venv.
- Check terminal logs for runtime errors.

### Speed/ETA not visible for some media
- Some sources/streams do not expose stable throughput metrics.
- Keep FFmpeg installed and updated.

### Post-processing errors
- Confirm `ffmpeg` is available in `PATH`.
- Verify with `ffmpeg -version`.

## Disclaimer

This tool is for lawful use only. You are responsible for complying with YouTube terms of service, copyright, and local laws.
