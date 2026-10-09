"""LLM clip selection with hard verification: quotes must exist in the transcript."""
import json
import re
from pathlib import Path
from typing import Callable

from . import config
from .analyze import chunks, render_text

SYSTEM = """You select standalone short-video clips from an interview transcript.
Rules:
- Pick complete question/answer or story units that make sense without the full video.
- Include the question if the answer needs it. Prefer a complete answer over a fixed length.
- start_text and end_text MUST be copied verbatim from the transcript (first and last ~8 words of the clip).
- Never invent dialogue. hook_idea is YOUR wording, not a quote.
- Score each dimension 0-10 honestly; say why a clip is weaker if it is.
Return ONLY JSON: {"clips":[{"topic":"","question_text":"","start_text":"","end_text":"",
"takeaway":"","hook_idea":"","context_needed":"","review_flags":[],"cta":"",
"scores":{"audience_match":0,"answer_completeness":0,"hook_clarity":0,"standalone":0,"specificity":0},
"rationale":""}]}
audience_match must be scored only from the research notes provided; if none, score it 5 and flag "no_research"."""


def _tok(s: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", s.lower())


def locate(words: list[dict], text: str, after: float = -1.0):
    """Find the word-index span matching `text`. Returns (first_idx, last_idx) or None."""
    target = _tok(text)
    if not target:
        return None
    toks = [_tok(w["w"]) for w in words]
    flat, owner = [], []
    for i, t in enumerate(toks):
        for x in t:
            flat.append(x)
            owner.append(i)
    n = len(target)
    for s in range(len(flat) - n + 1):
        if flat[s:s + n] == target and words[owner[s]]["start"] >= after:
            return owner[s], owner[s + n - 1]
    return None


def verify(clip: dict, words: list[dict]) -> dict | None:
    a = locate(words, clip.get("start_text", ""))
    if not a:
        return None
    b = locate(words, clip.get("end_text", ""), after=words[a[0]]["start"])
    if not b:
        return None
    s, e = words[a[0]]["start"], words[b[1]]["end"]
    if e <= s:
        return None
    clip = dict(clip)
    clip.update(start=round(s, 2), end=round(e, 2), duration=round(e - s, 2),
                speakers=sorted({w.get("speaker") or "SPEAKER" for w in words[a[0]:b[1] + 1]}),
                transcript=" ".join(w["w"] for w in words[a[0]:b[1] + 1]))
    flags = list(clip.get("review_flags", []))
    if clip["duration"] < config.CLIP_MIN:
        flags.append("short_clip")
    if clip["duration"] > config.CLIP_MAX:
        flags.append("long_clip")
    if any(w.get("score", 1) < 0.5 for w in words[a[0]:b[1] + 1]):
        flags.append("low_asr_confidence_words")
    clip["review_flags"] = sorted(set(flags))
    return clip


def weighted(scores: dict, weights: dict = config.WEIGHTS) -> float:
    return round(sum(weights[k] * float(scores.get(k, 0)) for k in weights) / sum(weights.values()), 1)


def anthropic_llm(system: str, user: str) -> str:
    import anthropic  # reads ANTHROPIC_API_KEY
    msg = anthropic.Anthropic().messages.create(
        model=config.LLM_MODEL, max_tokens=8000, system=system,
        messages=[{"role": "user", "content": user}])
    return "".join(b.text for b in msg.content if b.type == "text")


def _parse(raw: str) -> list[dict]:
    m = re.search(r"\{.*\}", raw, re.S)
    return json.loads(m.group(0)).get("clips", []) if m else []


def run(proj: Path, llm: Callable[[str, str], str] = anthropic_llm) -> Path:
    proj = Path(proj)
    words = json.loads((proj / "transcript" / "transcript.json").read_text())["words"]
    rpath = proj / "research" / "research.json"
    research = rpath.read_text() if rpath.exists() else "NO RESEARCH AVAILABLE"
    found, dropped = [], 0
    for t0, t1, win in chunks(words):
        user = f"RESEARCH NOTES (measured data vs. estimates are labelled):\n{research[:6000]}\n\nTRANSCRIPT {t0:.0f}s-{t1:.0f}s:\n{render_text(win)}"
        for c in _parse(llm(SYSTEM, user)):
            v = verify(c, words)
            if v is None:
                dropped += 1  # quote not found verbatim: treat as fabricated or misquoted
                continue
            v["score"] = weighted(v.get("scores", {}))
            found.append(v)
    uniq = {}
    for c in sorted(found, key=lambda c: -c["score"]):  # dedupe overlap-window repeats
        if not any(abs(c["start"] - u["start"]) < 5 and abs(c["end"] - u["end"]) < 5 for u in uniq.values()):
            uniq[len(uniq)] = c
    ranked = list(uniq.values())
    for i, c in enumerate(ranked, 1):
        c["clip_id"] = f"C{i:02d}"
    out = proj / "edit_decisions" / "clip_candidates.json"
    out.write_text(json.dumps({"status": "needs_human_review", "dropped_unverified": dropped,
                               "weights": config.WEIGHTS, "clips": ranked}, indent=1))
    return out
