# StreamNest — Feature Improvement Proposal

This document suggests yt-dlp-aligned feature improvements for StreamNest, modeled on
https://github.com/yt-dlp/yt-dlp and its documented options. Each item lists the relevant
yt-dlp option(s), what StreamNest currently lacks, and a suggested implementation approach.

See also: https://github.com/yt-dlp/yt-dlp#options (yt-dlp option reference).

**Status key:** ✅ Implemented · ⬜ Pending (not yet built)

---

## 1. Subtitles & closed captions

StreamNest downloads video/audio only. yt-dlp can fetch and embed subtitles, which is a core
feature for media archival.

| # | Feature | Status | yt-dlp option(s) | Suggested implementation |
|---|---------|--------|------------------|--------------------------|
| 1.1 | Write subtitle files | ✅ Implemented | `--write-subs` | `writesubtitles: true` in `_build_options` |
| 1.2 | Embed subtitles in file | ✅ Implemented | `--embed-subs` | `FFmpegEmbedSubtitle` postprocessor |
| 1.3 | Subtitle languages | ✅ Implemented | `--sub-langs` | `subtitleslangs` text field |
| 1.4 | Subtitle format conversion | ✅ Implemented | `--convert-subs` | `convertsubs` dropdown (SRT/VTT/TTML) |
| 1.5 | Embed chapters | ⬜ Pending | `--embed-chapters` | `FFmpegEmbedChapter` postprocessor |
| 1.6 | Split by chapters | ⬜ Pending | `--split-chapters` | `SplitChaptersFFmpeg` postprocessor |

---

## 2. Thumbnails & metadata

| # | Feature | Status | yt-dlp option(s) | Suggested implementation |
|---|---------|--------|------------------|--------------------------|
| 2.1 | Write thumbnail | ✅ Implemented | `--write-thumbnail` | `writethumbnail: true` in `_build_options` |
| 2.2 | Embed thumbnail | ✅ Implemented | `--embed-thumbnail` | `FFmpegEmbedThumbnail` postprocessor |
| 2.3 | Write info JSON | ⬜ Pending | `--write-info-json` | `writeinfojson: true` |
| 2.4 | Write description | ⬜ Pending | `--write-description` | `writedescription: true` |
| 2.5 | Write annotations | ⬜ Pending | `--write-annotations` | `writeannotations: true` |
| 2.6 | Add metadata (already partial) | ⬜ Pending | `--add-metadata` | FFmpegMetadata already used; extend with `metadatafromtitle` parsing options |

---

## 3. Playlist enhancements

StreamNest supports ranges (`1-5`, `1,3,7-10`) and selection, but lacks several yt-dlp playlist
controls.

| # | Feature | Status | yt-dlp option(s) | Suggested implementation |
|---|---------|--------|------------------|--------------------------|
| 3.1 | Playlist start index | ✅ Implemented | `--playlist-start` | `playliststart` int field |
| 3.2 | Playlist end index | ✅ Implemented | `--playlist-end` | `playlistend` int field |
| 3.3 | Reverse playlist order | ✅ Implemented | `--playlist-reverse` | `playlistreverse: true` checkbox |
| 3.4 | Random playlist order | ⬜ Pending | `--playlist-random` | `playlistrandom: true` checkbox |
| 3.5 | Skip unavailable items | ✅ Implemented | `--skip-unavailable` | `skipunavailable: true` (pair with `ignoreerrors`) |
| 3.6 | No abort on error | ✅ Implemented | `--no-abort-on-error` | `noabortonerror: true` |
| 3.7 | Max downloads | ✅ Implemented | `--max-downloads` | `maxdownloads` int field |
| 3.8 | Download archive | ✅ Implemented | `--download-archive` | `downloadarchive` path field |

---

## 4. Network, auth & geo

| # | Feature | Status | yt-dlp option(s) | Suggested implementation |
|---|---------|--------|------------------|--------------------------|
| 4.1 | Cookies from browser | ✅ Implemented | `--cookies-from-browser` | `cookiesfrombrowser` dropdown |
| 4.2 | Cookies file | ✅ Implemented | `--cookies` | `cookies` text field |
| 4.3 | Proxy | ✅ Implemented | `--proxy` | `proxy` text field |
| 4.4 | Geo-bypass | ✅ Implemented | `--geo-bypass` | `geobypass: true` checkbox |
| 4.5 | Geo verification proxy | ⬜ Pending | `--geo-verification-proxy` | `geoverificationproxy` |
| 4.6 | User-Agent / Referer | ⬜ Pending | `--user-agent`, `--referer` | Text fields; `useragent`, `referer` |
| 4.7 | Socket timeout | ⬜ Pending | `--socket-timeout` | Fail fast on unresponsive hosts |
| 4.8 | Rate limit | ✅ Implemented | `--limit-rate` | Cap download speed (bandwidth) |
| 4.9 | Sleep interval | ✅ Implemented | `--sleep-interval`, `--sleep-requests` | Sleep interval / sleep requests text fields |
| 4.10 | Concurrent fragments | ⬜ Pending | `--concurrent-fragment-downloads` | Faster HLS/DASH fragment fetch |
| 4.11 | External downloader | ⬜ Pending | `--external-downloader` (aria2c) | Detect aria2c; `external downloader` + args |
| 4.12 | Retry on HTTP errors | ⬜ Pending | `--retry-on-http-errors` | Retry 4xx/5xx where sensible |
| 4.13 | Fragment retries | ⬜ Pending | `--fragment-retries` | Retry failed HLS fragments |

---

## 5. Output & file control

| # | Feature | yt-dlp option(s) | Why add it | Suggested implementation |
|---|---------|------------------|------------|--------------------------|
| 5.1 | Custom output template | `-o / --output` | Full control over filenames/paths | `outtmpl` text field (validate against path traversal) |
| 5.2 | No overwrites | `--no-overwrites` | Skip existing files | `nooverwrites: true` |
| 5.3 | Force overwrites | `--force-overwrites` | Replace existing files | `forceoverwrites: true` |
| 5.4 | No `.part` files | `--no-part` | Write directly to final name | `nopart: true` |
| 5.5 | Preserve mtime | `--no-mtime` / set mtime | Keep remote modification time | `updatetime` / mtime handling |
| 5.6 | Auto-number | `--autonumber` | Sequence files | `autonumber`, `autonumbersize`, `autonumberstart` |
| 5.7 | Output NA placeholder | `--output-na-placeholder` | Token for missing metadata | `outputnaplaceholder` text |
| 5.8 | Restrict filenames | (already done) | `--restrict-filenames` exists | Keep existing behavior |
| 5.9 | Fixup policy | `--fixup` | Audio repair: detect/warn/never | `fixup` dropdown (`detect_or_warn`, `warn`, `never`) |

---

## 6. Quality & format selection

| # | Feature | yt-dlp option(s) | Why add it | Suggested implementation |
|---|---------|------------------|------------|--------------------------|
| 6.1 | Format sort | `--format-sort` | Prefer codec/resolution/fps | `formatsort` field (e.g. `res,ext:mp4:mime, fps, hdr:12, source`) |
| 6.2 | Format sort force | `--format-sort-force` | Force sort even when unspecified | `formatsortforce` |
| 6.3 | Prefer free formats | `--prefer-free-formats` | Prefer open codecs | `preferfreeformats: true` |
| 6.4 | Check formats | `--check-formats` | Validate format selection without download | Dry-run button |
| 6.5 | List available formats | `-F / --list-formats` | Show all formats in UI | Surface raw format list in a debug/log view |
| 6.6 | Recode video/audio | `--recode-video`, `--recode-audio` | Transcode after download | `recodevideo`, `recodeaudio` dropdowns |
| 6.7 | Video-only / audio-only | `-f` selection | Download without merging | Add "video only" and "audio only (no convert)" modes |

---

## 7. yt-dlp engine management

| # | Feature | Status | yt-dlp option(s) | Suggested implementation |
|---|---------|--------|------------------|--------------------------|
| 7.1 | Self-update | ✅ Implemented | `yt-dlp -U` | "Update yt-dlp" button running `pip install -U yt-dlp` |
| 7.2 | Version check | ✅ Implemented | `yt-dlp --version` | Show yt-dlp version alongside FFmpeg version |
| 7.3 | Verbose mode | ✅ Implemented | `--verbose` | Toggle for `verbose: true` in yt-dlp opts |
| 7.4 | No warnings | ✅ Implemented | `--no-warnings` | Already partly used; expose toggle |

---

## 8. UX / history / state improvements

| # | Feature | Why add it | Suggested implementation |
|---|---------|------------|--------------------------|
| 8.1 | Download queue | Download multiple URLs sequentially instead of one at a time | Queue model + `DownloaderService` serialized worker |
| 8.2 | Pause/resume | Pause active download and resume later | yt-dlp `continuedl` already set; add pause signal + resume from `.part` |
| 8.3 | Per-download rename | Rename output before saving | `outtmpl` override per item or post-download rename |
| 8.4 | History export | Export history as JSON/CSV | `HistoryStore.load()` → export dialog |
| 8.5 | History search/filter | Find past downloads by title/URL/platform | Filter bar on History tab |
| 8.6 | Estimated size before download | Show approximate file size | Use `filesize_approx` from format extraction |
| 8.7 | Recent downloads preview | Already present; add "re-download" action | Reuse a history entry's `DownloadRequest` |
| 8.8 | Download scheduling | Start download at a given time | Optional future enhancement |

---

## 9. Security hardening (aligned with existing model)

StreamNest already validates URLs, blocks localhost/private IPs, caps size at 5 GB, and
restricts save directories. Add:

| # | Feature | Why | Implementation |
|---|---------|-----|----------------|
| 9.1 | Cookie file validation | Prevent reading arbitrary files via `--cookies` | Resolve within allowed roots only; reject paths outside home/Downloads/TMPDIR |
| 9.2 | Proxy allowlist | Prevent proxying to internal networks | Block private/reserved proxy destinations |
| 9.3 | Custom template sanitization | Prevent path traversal via `-o` | Reject `..`, absolute paths, drive letters; force placement under save_dir |
| 9.4 | Download-archive path guard | Prevent archive escape | Same root validation as save directories |

---

## Suggested rollout order (MVP first)

1. **Subtitles write/embed** + **thumbnail write/embed** — high user value, maps cleanly to existing FFmpeg postprocessor pipeline (`services/downloader.py` `_build_options`).
2. **Playlist start/end/skip-unavailable/no-abort-on-error** — extends existing playlist range support (`services/format_extractor.py` `normalize_playlist_range`).
3. **Cookies from browser/file** + **proxy** — unlocks restricted content.
4. **Rate limit** + **sleep interval** — bandwidth politeness.
5. **Download archive** + **queue** — batch workflow.
6. **yt-dlp self-update/version** + **format sort** — engine parity.

Files most likely to change:
- `services/downloader.py` — `DownloadRequest` fields, `_build_options`, postprocessor hooks
- `services/format_extractor.py` — `QualityOption`/`PlaylistInfo` additions, playlist range controls
- `utils/validators.py` — cookie/proxy/template validation
- `utils/file_manager.py` — archive path validation
- `ui/home/*` — new controls (checkboxes, fields, dropdowns)
- `state/app_state.py` — new state fields

---

## Reference

- yt-dlp options: https://github.com/yt-dlp/yt-dlp#options
- yt-dlp postprocessors: FFmpegMetadata, FFmpegEmbedSubtitle, FFmpegEmbedThumbnail, FFmpegEmbedChapter, SplitChaptersFFmpeg, FFmpegVideoRemuxer, FFmpegExtractAudio
- StreamNest changelog: `changelog.md`
