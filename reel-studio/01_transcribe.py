#!/usr/bin/env python3
"""Step 1 - transcribe a video locally (nothing is uploaded).

    python 01_transcribe.py "C:/Users/you/Downloads/video1669769194.mp4"

Writes next to the video (or --out DIR):
    transcript.json   word-level timestamps, used by the renderer
    transcript.txt    readable, timestamped text - paste THIS to Claude so it can pick the reels
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile


def mmss(t):
    return f"{int(t // 60):02d}:{t % 60:04.1f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", default=None, help="output folder (default: ./work)")
    ap.add_argument("--model", default="small", help="tiny|base|small|medium|large-v3 (bigger = slower, better)")
    ap.add_argument("--language", default=None, help="e.g. en (default: auto-detect)")
    a = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH. Install it first (see README).")
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("Missing dependency. Run:  pip install faster-whisper")

    out = a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "work")
    os.makedirs(out, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        wav = os.path.join(td, "audio.wav")
        print("extracting audio...")
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", a.video, "-vn", "-ac", "1",
                               "-ar", "16000", wav])
        print(f"loading Whisper '{a.model}' (first run downloads the model once)...")
        model = WhisperModel(a.model, device="auto", compute_type="auto")
        print("transcribing (this is the slow part; ~0.3-1x realtime on CPU)...")
        segs, info = model.transcribe(wav, word_timestamps=True, vad_filter=True,
                                      language=a.language, condition_on_previous_text=False)
        words, lines = [], []
        for s in segs:
            lines.append(f"[{mmss(s.start)}] {s.text.strip()}")
            for w in s.words or []:
                words.append(dict(w=w.word.strip(), start=round(w.start, 3), end=round(w.end, 3)))
            print(lines[-1][:110])

    dur = words[-1]["end"] if words else 0
    with open(os.path.join(out, "transcript.json"), "w", encoding="utf-8") as f:
        json.dump(dict(source=os.path.abspath(a.video), duration=dur, language=info.language, words=words),
                  f, ensure_ascii=False)
    with open(os.path.join(out, "transcript.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nDone: {len(words)} words, language={info.language}")
    print(f"Paste the contents of {os.path.join(out, 'transcript.txt')} to Claude.")


if __name__ == "__main__":
    main()
