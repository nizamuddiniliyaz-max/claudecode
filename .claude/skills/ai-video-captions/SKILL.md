---
name: ai-video-captions
description: >-
  Burn animated, word-by-word captions into a video using a free, local, open-source tool
  (nicolaigaina/ai-video-captions, MIT). Six styles: hormozi, mrbeast, karaoke, minimal, bounce,
  classic. Local faster-whisper transcription, ASS subtitles, FFmpeg burn-in, no cloud, no API key.
  Use when someone wants captions on a clip or reel, wants to test caption styles, asks for
  Hormozi/MrBeast-style subtitles, or wants captions added without CapCut or a subscription.
  Captions only: it does not cut silences, clip long videos, reframe to 9:16, or add graphics.
  For those use reel-studio (repo folder) or captions-and-clipping.
---

# ai-video-captions

Vendored upstream app in `app/` (commit `bd87ac7`, MIT, see `licenses/`). It is a **self-hosted
web app + REST API that runs on the user's own computer**. It does not run inside Claude. Claude's job
is to get the user running it, pick a style, and help with the output.

## What it does
Upload a video -> faster-whisper transcribes with word timestamps -> animated ASS subtitles
-> FFmpeg burns them in -> `*_captioned.mp4` (CRF 18, original audio).

## Styles (`captionStyle`)
| id | look |
|---|---|
| `hormozi` | bold cyan highlights, thick outline |
| `mrbeast` | yellow text, orange highlights, extra thick outline |
| `karaoke` | colour wipe left to right |
| `minimal` | subtle scaling, near-white highlight |
| `bounce` | playful bounce, bright colours |
| `classic` | traditional yellow highlight, Anton font |

`captionPosition` = 5-50, percent up from the bottom (default to ~35-40 so it sits below centre,
clear of the Instagram UI).

## Run it (user's machine)
Docker (easiest): from `.claude/skills/ai-video-captions/app/`
```
docker compose up
```
then open http://localhost:3000, drop the video, pick a style, download the result.

No Docker: needs Python 3.11+, Node 20+, FFmpeg, then `make setup` and `make dev`.

## Batch via the API (when Claude Code runs on the same machine as the app)
```
curl -F "file=@clip.mp4" -F "captionStyle=hormozi" -F "captionPosition=38" http://localhost:5000/api/process
curl http://localhost:5000/api/status/<jobId>          # poll until "completed"
curl -o clip_captioned.mp4 http://localhost:5000/api/download/<jobId>
```
Full reference: `app/docs/API.md`.

## Limits and settings (`app/.env.example` -> `.env`)
- Defaults: 500 MB and **30 minutes** per file, Whisper model `base`. A 30-minute Zoom recording is
  right at the limit; raise `MAX_FILE_SIZE_MB` / `MAX_DURATION_MINUTES` or caption the clips, not the
  full recording.
- For accuracy on names and jargon set `WHISPER_MODEL_SIZE=small` or `medium` (slower, more RAM).
- Accepts MP4, MOV, WebM. Output files are deleted after `OUTPUT_TTL_HOURS` (24): download promptly.
- Proof-read the captions before posting; Whisper mishears names. Edit and re-run if needed.

## Workflow notes
1. Cut/clip the long video first (CapCut, or reel-studio). Caption the finished 9:16 clips.
2. To compare styles, run the same 20-30 s clip through all six and watch on a phone.
3. Do not caption client/NDA video through any hosted version; this local copy keeps files on the machine.
