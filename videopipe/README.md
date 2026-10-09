# videopipe (milestone 1)

Local-first: one video in, then a timestamped transcript, edit proposals, research notes and ranked clip candidates. No rendering yet. The original video is never modified.

## What leaves your laptop
| Command | Off-device? |
|---|---|
| `init`, `transcribe`, `analyze`, `report` | Nothing. (`transcribe` downloads models once from Hugging Face.) |
| `research` | Search query strings, to the YouTube Data API |
| `candidates` | Transcript text, to the Anthropic API |

## Setup (Windows, 8 GB RAM)
1. Install Python 3.11+, FFmpeg (`winget install Gyan.FFmpeg`), and git.
2. In this folder:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -e ".[transcribe,llm,dev]"
   ```
3. Keys (set as environment variables, never commit them):
   - `ANTHROPIC_API_KEY` for `candidates`
   - `HF_TOKEN` for speaker labels (accept the terms for `pyannote/speaker-diarization-community-1` on Hugging Face first)
   - `YOUTUBE_API_KEY` (optional) for `research`

## Run
```
vp init "C:\path\interview.mp4" --root C:\VideoProjects
vp transcribe C:\VideoProjects\interview --model small      # add --no-diarize to skip speakers
vp analyze    C:\VideoProjects\interview
vp research   C:\VideoProjects\interview "hyrox pacing" "hyrox sled push technique"
vp candidates C:\VideoProjects\interview
vp report     C:\VideoProjects\interview                      # reports\clip_candidates.md
```
Run the steps one at a time on an 8 GB machine, and close other apps during `transcribe`.

## Safety rules built in
- Candidate quotes must match the transcript word for word, or the clip is dropped (the count is reported).
- Cut proposals are proposals only; nothing is deleted.
- Hook ideas are labelled as model-written, not quotes.
- Research records only data actually retrieved, with query, URL, access date and source.

## Test status
`python -m pytest` covers ingest, cut proposals, quote verification, scoring and the full candidates flow with a stubbed LLM.
**Not yet run:** `transcribe.py` (WhisperX API names may differ by version) and `research.py` (needs network and a key). Expect small fixes on first real run.
