# Local-First AI Video Repurposing: Tool Research and Proposed Architecture

Research date: 2026-10-09. Nothing was installed or executed. Evidence comes from GitHub pages read during this session plus web search snippets. Anything not verified is marked **(unverified)**.

## 1. Executive summary

**Achievable fully locally**
- Transcription with word-level timestamps and speaker labels.
- Silence, filler and repeat detection (as proposals).
- Cutting, loudness leveling and 9:16 reframing with face detection.
- Styled captions, covers, motion graphics and end cards from HTML templates.
- Semantic clip ranking, if you run a local LLM (Ollama or LM Studio). Quality will be below a hosted frontier model.

**Needs web or cloud access**
- Research: YouTube metadata, Reddit threads, Google Trends, articles.
- Best-quality clip reasoning and hook writing (hosted LLM, optional).
- Speaker diarization models need a one-time Hugging Face login to download. Inference then runs offline.

**Important finding:** the most popular Claude skill for this job, `browser-use/video-use`, sends audio to ElevenLabs for transcription. That breaks your local-first rule. Reuse its ideas (cut-boundary self-checks, audio fades), not its transcription path.

## 2. GitHub shortlist (verified)

| Tool | Type | Local? | License | Maintenance evidence | Verdict |
|---|---|---|---|---|---|
| [m-bain/whisperX](https://github.com/m-bain/whisperX) | Python CLI/lib | Local (GPU optional; CPU int8 works) | BSD-2-Clause | v3.8.6 (May 2026); commit Sep 26, 2026; 24.4k stars | **Use.** Word timestamps (wav2vec2 alignment) plus pyannote diarization in one pass. Needs HF token and accepting the pyannote model terms. |
| [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Python lib | Local | MIT | v1.2.1 (Oct 2025); commit Oct 6, 2026 | Fallback if whisperX alignment or diarization is a pain. Already inside whisperX. |
| [pyannote/pyannote-audio](https://github.com/pyannote/pyannote-audio) | Python lib | Local after model download | MIT code; model `community-1` is gated on HF (CC-BY-4.0 per whisperX README) | 4.0.7 (Jun 30, 2026) | Use via whisperX. Avoid the paid "precision-2" API (cloud). |
| [ggml-org/whisper.cpp](https://github.com/ggml-org/whisper.cpp) | C++ CLI | Local, runs well on CPU/Apple Silicon | MIT | v1.9.5 (Oct 6, 2026) | Good CPU or Mac alternative. No diarization built in. |
| [WyattBlue/auto-editor](https://github.com/WyattBlue/auto-editor) | CLI (Nim) | Local | Unlicense | tag 31.7.2 (Oct 3, 2026) | Use for **silence/motion analysis only**. It also ships a `skills/` folder (contents not inspected). |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | Node CLI + **21 agent skills / Claude Code plugin** | Local renderer (headless Chrome + FFmpeg). Optional HeyGen cloud and Lambda rendering exist; avoid. | Apache-2.0 | tag v0.8.143 (Oct 8, 2026); 5,421 commits | **Use** for captions, covers, graphics, end cards. Includes `/embedded-captions` and `/talking-head-recut` skills. Very fast release cadence, so pin a version. HeyGen is the maker; comparisons with Remotion are promotional. |
| [remotion-dev/remotion](https://github.com/remotion-dev/remotion) + [remotion-dev/skills](https://github.com/remotion-dev/skills) | React lib + agent skills | Local | **Custom, non-OSI.** Free for individuals and for-profits up to 3 employees; company license above that (price at remotion.pro, not verified). | tag v4.0.534 (Oct 7, 2026) | Alternative to HyperFrames if you prefer React. Redundant, so pick one. Free for you today; check terms if Bijen's business grows. |
| [browser-use/video-use](https://github.com/browser-use/video-use) | **Claude Code skill** (SKILL.md + helpers) | **Not local**: ElevenLabs Scribe for transcription. Rendering is local ffmpeg. | MIT | commit Oct 8, 2026; 28.5k stars; no releases | **Study, don't adopt as core.** Good reference for the skill layout and the per-cut self-check. |
| [linzzzzzz/openclip](https://github.com/linzzzzzz/openclip) | App + Claude skill `video-clip-extractor` | Partly: local Whisper; LLM via Qwen/OpenRouter/etc. or local OpenAI-compatible server | MIT | commit Aug 24, 2026; v0.6.0; 569 stars | **Reference only.** Closest end-to-end example of the transcribe → rank → clip → cover pipeline. Small community. |
| [anthropics/skills](https://github.com/anthropics/skills) | Skills repo | n/a | Mixed (many Apache-2.0; docx/pdf/pptx/xlsx source-available) | 180k stars | **No video skill.** Useful for `skill-creator` and `mcp-builder` when you author the custom skills. |
| [ultralytics](https://github.com/ultralytics/ultralytics) | Python lib | Local | **AGPL-3.0** (paid enterprise license available) | Active | **Avoid for reframing.** AGPL is a license risk. |
| [google-ai-edge/mediapipe](https://github.com/google-ai-edge/mediapipe) | Python lib | On-device, but its Tasks APIs send performance metrics to Google (per privacy notice) | Apache-2.0 | Notice updated Jun 5, 2026 | Candidate for face detection. Check telemetry. |
| [serengil/retinaface](https://github.com/serengil/retinaface) | Python lib | Local (ONNX) | MIT (weights license not verified) | 238 commits, 2 open issues | Simpler alternative for face boxes. |
| [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) | CLI | Local, fetches from YouTube | Unlicense | Nightly builds recommended | Optional, for public metadata only. README has no ToS guidance; check YouTube terms. |
| [praw-dev/praw](https://github.com/praw-dev/praw) | Python lib | Calls Reddit's hosted API | BSD-2-Clause | Active | Use for public Reddit questions. Reddit's API terms **could not be read** (blocked), so confirm before relying on them. |
| [GeneralMills/pytrends](https://github.com/GeneralMills/pytrends) | Python lib | Unofficial Google Trends scraper | License type not seen | **Archived Apr 17, 2025, read-only** | **Do not use.** Archived, unofficial, unknown rate limits. |
| [gorakhargosh/watchdog](https://github.com/gorakhargosh/watchdog) | Python lib | Local | Apache-2.0 | Copyright through 2026 | Use for the input-folder watcher. |
| [n8n-io/n8n](https://github.com/n8n-io/n8n) | App | Self-hostable | Sustainable Use License (source-available, not OSI) | Active | **Skip.** Overkill and not open source. Plain Python plus watchdog is enough. |

**Unverified or dropped**
- `tkhudson/openshorts` returned 404 when fetched. A search snippet mentioned it, but I can't confirm it exists. Don't use it.
- Skate, SupoClip (AGPL per snippet), OpenClipV, AutoShorts (uses Deepgram, so not offline): seen only in search snippets and not inspected.
- Tella skills and `affaan-m/ecc` video-editing skill: snippets only.
- Social-media skills already in your Claude environment (`ig-reel`, `hook-writer`, `ig-caption`, `captions-and-clipping`, `ig-repurpose`) can write hooks, captions and CTAs. I did not inspect them here.

## 3. Recommended stack (smallest reliable set)

| Job | Component |
|---|---|
| Ingest/watch | Python + watchdog |
| Media probe, cut, loudnorm, concat, encode | ffmpeg/ffprobe (local) |
| Transcript + word timing + speakers | WhisperX (faster-whisper + wav2vec2 + pyannote) |
| Silence/filler proposals | auto-editor (analysis) + custom filler/repeat detector over the transcript |
| Face tracking for 9:16 | MediaPipe or RetinaFace (decide after checking telemetry and weights terms) |
| Captions, covers, graphics, end cards | HyperFrames (HTML templates, Apache-2.0) |
| Research | YouTube Data API (official), PRAW, optional web search; hosted LLM for synthesis |
| Clip reasoning | Claude (hosted, optional) or a local LLM via Ollama |
| Orchestration | Claude Code skills calling Python CLIs; JSON files as the interface |

## 4. Architecture

```
source/video.mp4 (read-only, hashed)
   │  ffprobe → metadata.json
   ▼
extract audio → WhisperX → transcript.json (words, speakers)
   ▼
analyze: topics, Q&A pairs, claims, filler/silence flags ─► edit_decisions/cuts_proposed.json
   ▼                                                        │
research (web, labeled off-device) ─► research/report.json  │
   ▼                                                        ▼
match topics ↔ transcript, score 5 dimensions ─► clip_candidates.json + ranked report
   ▼ human approval gate
YouTube cut: ffmpeg from approved cuts + loudnorm ─► renders/youtube/
Reel render: cut → face-tracked 9:16 → HyperFrames captions/hook/CTA → renders/reels/ + .srt + cover
   ▼
QC: caption-vs-audio diff, loudness/clipping, ffprobe checks, cut-context check, source links
   ▼
review queue (reports/) — no publishing
```

Every artifact carries source timestamps. The only edit instruction format is JSON, so renders are reproducible.

## 5. Claude skill plan

Reuse: `hyperframes` skills (captions, graphics), `skill-creator`, `mcp-builder`, and your existing social skills for hook/caption/CTA drafting.

Create (custom):
```
.claude/skills/
  vp-ingest/SKILL.md          # project folder, hash, ffprobe, watcher
  vp-transcribe/SKILL.md      # WhisperX wrapper, schema for transcript.json
  vp-analyze/SKILL.md         # topics, Q&A, filler/silence proposals (never auto-delete)
  vp-research/SKILL.md        # query log, source URLs, access dates, metric provenance
  vp-clip-select/SKILL.md     # rubric (25/25/20/15/15), context rules, no invented quotes
  vp-render/SKILL.md          # ffmpeg + reframe + HyperFrames templates
  vp-qc/SKILL.md              # checklist from section 8 of your brief
scripts/                      # Python CLIs, each with --help and JSON in/out
templates/                    # HyperFrames compositions (cover, captions, CTA, series card)
```
Each SKILL.md states inputs, outputs, schema paths, and hard rules (originals untouched, no fabricated dialogue or metrics, hooks labeled as written by the model).

## 6. Local requirements

- OS: Linux/macOS/Windows all supported by the core tools. HyperFrames needs Node 22+ and FFmpeg.
- GPU: optional. WhisperX large-v2 reportedly fits in under 8 GB VRAM; CPU int8 works but is slower (speed not measured here). I need your hardware (CPU, RAM, GPU/VRAM, OS) for a firm model-size recommendation.
- Disk: budget roughly 3–5× the source size for intermediates, plus several GB of models (not measured).
- Likely bottlenecks: transcription plus diarization, final encodes, headless-Chrome frame rendering for graphics.

## 7. Cost and privacy

- Fully local: ingest, transcription, diarization (after model download), analysis, cutting, reframing, captions, covers, QC.
- Off-device only if you choose: transcript text sent to a hosted LLM; web searches; YouTube API calls; Reddit API calls. The source video never needs to leave your machine.
- Costs: local tools are free. Hosted LLM and search are pay-per-use. YouTube Data API default quota is about 10,000 units/day per Google's docs snippet, which I could not open directly **(unverified)**.
- Avoid by default: ElevenLabs transcription (video-use), HeyGen cloud render, pyannote precision-2 API, Remotion paid license if you outgrow the free tier.

## 8. Roadmap

1. Ingest + transcription + schema (WhisperX).
2. Analysis + filler/silence proposals + clip candidates (local or hosted LLM). **No rendering yet.**
3. Research module with provenance fields.
4. YouTube cleaned cut with approved EDL.
5. Basic Reel render: cut, reframe, captions, cover.
6. Templates, selective motion graphics, CTA cards.
7. QC automation and review queue.

## 9. Risks and limits

- Public view counts don't show retention. Trend claims need dated sources, and pytrends is dead, so Google Trends has no clean programmatic path.
- Whisper makes errors on names, sports terms, numbers and units. Keep a glossary (HYROX, VO2 max, zone 2, and so on) and check captions by hand.
- Diarization errs on overlapping speech. Reframing needs face tracking plus a speaker map and will mis-cut sometimes.
- LLM clip ranking is a judgment call, not a prediction of virality.
- HyperFrames releases almost daily, so pin versions. Remotion's license may change in 5.0.
- Reddit and YouTube API terms need a human read before going live.
- GitHub pages didn't show most last-commit dates, so maintenance evidence is partly release tags.

## 10. First milestone (proof of concept)

One 35–40 minute video in, with no rendering:
1. Project folder, hash, ffprobe metadata.
2. WhisperX transcript with word timestamps and speakers.
3. Topic and Q&A extraction, plus cut proposals as JSON.
4. Research report for 5–8 topics with source URLs and access dates.
5. Ranked table of about 15 clip candidates with source start/end times and exact transcript text.

Success: you review the table and agree that most top picks are real, standalone answers.

## Questions before building
1. Hardware: OS, CPU, RAM, GPU/VRAM?
2. Is a hosted LLM acceptable for ranking and research, or must everything stay local?
3. HyperFrames (HTML) or Remotion (React) for graphics? I recommend HyperFrames.
