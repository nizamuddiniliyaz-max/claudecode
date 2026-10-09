"""Project folders, hashing, metadata. The source file is copied, never modified."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

SUBDIRS = [
    "source", "transcript", "research", "edit_decisions",
    "assets/captions", "assets/graphics", "assets/covers",
    "renders/youtube", "renders/reels", "reports",
]


def sha256(path: Path, block: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(block):
            h.update(chunk)
    return h.hexdigest()


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    raw = json.loads(out)
    video = next((s for s in raw["streams"] if s["codec_type"] == "video"), None)
    audio = [s for s in raw["streams"] if s["codec_type"] == "audio"]
    meta = {
        "duration_s": float(raw["format"].get("duration", 0)),
        "audio_tracks": len(audio),
        "audio_codecs": [a.get("codec_name") for a in audio],
    }
    if video:
        num, _, den = video.get("avg_frame_rate", "0/1").partition("/")
        meta.update(
            width=video.get("width"), height=video.get("height"),
            fps=round(int(num) / int(den), 3) if den and int(den) else None,
            video_codec=video.get("codec_name"),
        )
    return meta


def init_project(video: Path, root: Path, name: str | None = None) -> Path:
    video = Path(video)
    if not video.is_file():
        raise FileNotFoundError(video)
    proj = Path(root) / (name or video.stem)
    for d in SUBDIRS:
        (proj / d).mkdir(parents=True, exist_ok=True)
    dest = proj / "source" / video.name
    if not dest.exists():
        shutil.copy2(video, dest)
    dest.chmod(0o444)  # read-only guard on the working copy
    meta = {"file": dest.name, "sha256": sha256(dest), "bytes": dest.stat().st_size, **probe(dest)}
    if meta["sha256"] != sha256(video):
        raise RuntimeError("copy hash mismatch")
    (proj / "metadata.json").write_text(json.dumps(meta, indent=2))
    return proj


def source_file(proj: Path) -> Path:
    meta = json.loads((Path(proj) / "metadata.json").read_text())
    return Path(proj) / "source" / meta["file"]
