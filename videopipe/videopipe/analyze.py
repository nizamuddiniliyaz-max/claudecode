"""Edit proposals from the transcript. Everything here is a PROPOSAL; nothing is deleted."""
import json
import re
from pathlib import Path

from . import config


def _norm(w: str) -> str:
    return re.sub(r"[^\w']", "", w.lower())


def propose_cuts(words: list[dict]) -> list[dict]:
    props = []
    for i, w in enumerate(words):
        n = _norm(w["w"])
        if n in config.FILLERS:
            props.append({"type": "filler", "start": w["start"], "end": w["end"], "text": w["w"],
                          "idx": i, "confidence": "medium",
                          "note": "Check it is not a meaningful reaction or part of a hesitation worth keeping."})
        if i and n and n == _norm(words[i - 1]["w"]) and n not in config.FILLERS:
            props.append({"type": "repeat", "start": words[i - 1]["start"], "end": words[i - 1]["end"],
                          "text": words[i - 1]["w"], "idx": i - 1, "confidence": "low",
                          "note": "Immediate repeat; could be emphasis."})
        if i:
            gap = w["start"] - words[i - 1]["end"]
            if gap >= config.MIN_PAUSE:
                props.append({"type": "pause", "start": words[i - 1]["end"], "end": w["start"],
                              "text": f"{gap:.1f}s", "idx": i, "confidence": "low",
                              "note": "Long pause; may be a natural beat before an answer."})
    return props


def chunks(words: list[dict], size: float = config.CHUNK_SECONDS, overlap: float = config.CHUNK_OVERLAP):
    """Yield (start, end, words) windows with overlap so Q&A pairs are not split."""
    if not words:
        return
    t, end = words[0]["start"], words[-1]["end"]
    while t < end:
        win = [w for w in words if t <= w["start"] < t + size]
        if win:
            yield t, t + size, win
        if t + size >= end:
            break
        t += size - overlap


def render_text(words: list[dict]) -> str:
    """Timestamped, speaker-labelled text for LLM input. Index prefix lets quotes be verified."""
    lines, cur, buf, t0 = [], None, [], None
    for w in words:
        sp = w.get("speaker")
        if sp != cur and buf:
            lines.append(f"[{t0:.1f}] {cur or 'SPEAKER'}: {' '.join(buf)}")
            buf = []
        if not buf:
            t0, cur = w["start"], sp
        buf.append(w["w"])
        if len(buf) >= 40 and w["w"].endswith((".", "?", "!")):
            lines.append(f"[{t0:.1f}] {cur or 'SPEAKER'}: {' '.join(buf)}")
            buf = []
    if buf:
        lines.append(f"[{t0:.1f}] {cur or 'SPEAKER'}: {' '.join(buf)}")
    return "\n".join(lines)


def run(proj: Path) -> Path:
    tr = json.loads((Path(proj) / "transcript" / "transcript.json").read_text())
    out = Path(proj) / "edit_decisions" / "cuts_proposed.json"
    props = propose_cuts(tr["words"])
    out.write_text(json.dumps({"status": "proposal_only", "count": len(props), "proposals": props}, indent=1))
    return out
