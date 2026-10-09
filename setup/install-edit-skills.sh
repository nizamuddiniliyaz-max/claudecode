#!/usr/bin/env bash
# One-shot local setup for the /edit, /virality, /build skills (Mac/Linux/WSL/Git Bash)
set -e
echo "==> Checking ffmpeg"
if ! command -v ffmpeg >/dev/null; then
  if command -v brew >/dev/null; then brew install ffmpeg
  elif command -v apt-get >/dev/null; then sudo apt-get update && sudo apt-get install -y ffmpeg
  elif command -v winget >/dev/null; then winget install -e --id Gyan.FFmpeg
  else echo "Install ffmpeg manually: https://ffmpeg.org/download.html"; exit 1; fi
fi
echo "==> Installing faster-whisper (filler-word detection)"
PY=$(command -v python3 || command -v python)
"$PY" -m pip install --user faster-whisper
echo "==> Installing skills to ~/.claude/skills"
TMP=$(mktemp -d)
git clone -q https://github.com/Jakeschincariol/master-skills.git "$TMP/ms"
mkdir -p ~/.claude/skills
cp -r "$TMP/ms/skills/"* ~/.claude/skills/
rm -rf "$TMP"
echo "==> Doctor check"
"$PY" ~/.claude/skills/edit/tools/probe.py --doctor || true
echo "Done. Open Claude Code in your video's folder and run: /edit yourfile.mp4"
