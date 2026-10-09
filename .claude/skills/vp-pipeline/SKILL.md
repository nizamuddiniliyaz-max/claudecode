---
name: vp-pipeline
description: Run the local-first video repurposing pipeline (videopipe) on an interview video to get a transcript, cut proposals, research notes and ranked Reel candidates. Use when the user says "process this interview", "find clips in this video", or "run the video pipeline".
---

# vp-pipeline

Drives the `vp` CLI in `videopipe/`. Milestone 1 stops at ranked candidates; never render or publish without approval.

## Steps
1. `vp init <video> --root <VideoProjects>`. Confirm metadata.json looks right (duration, resolution, one audio track).
2. `vp transcribe <project> --model small`. Spot-check names, numbers and sports terms against the audio. Fix a glossary if ASR is wrong.
3. `vp analyze <project>`. Treat cuts_proposed.json as suggestions; review pauses and repeats before using any.
4. Research: propose 5-8 topics from the transcript, then `vp research <project> "<query>" ...`. Tell the user queries are sent to YouTube. Add any web findings to research/manual_notes.md with URL and access date. Never describe a topic as trending without a dated source.
5. `vp candidates <project>` (sends transcript text to the Anthropic API; say so first), then `vp report <project>`.
6. Present the ranked table. Flag low-confidence clips and anything dropped as unverified. Ask which clips to approve.

## Rules
- Never edit or delete files in source/.
- Hooks are model-written; never present them as quotes.
- Do not invent metrics, quotes or engagement figures.
- Stop for human approval before any render or any use of the cloud beyond the two calls above.
