import json
from pathlib import Path


def ts(s: float) -> str:
    return f"{int(s // 60):02d}:{s % 60:05.2f}"


def run(proj: Path) -> Path:
    proj = Path(proj)
    data = json.loads((proj / "edit_decisions" / "clip_candidates.json").read_text())
    L = [f"# Ranked clip candidates: {proj.name}", "",
         f"Status: **{data['status']}** · unverified quotes dropped: {data['dropped_unverified']}", "",
         "| ID | Score | Start–End | Dur | Speakers | Topic | Flags |", "|---|---|---|---|---|---|---|"]
    for c in data["clips"]:
        L.append(f"| {c['clip_id']} | {c['score']} | {ts(c['start'])}–{ts(c['end'])} | {c['duration']:.0f}s | "
                 f"{', '.join(c['speakers'])} | {c['topic']} | {', '.join(c['review_flags']) or '-'} |")
    for c in data["clips"]:
        L += ["", f"## {c['clip_id']} · {c['topic']} · {c['score']}/10",
              f"**Question:** {c.get('question_text', '')}",
              f"**Takeaway:** {c.get('takeaway', '')}",
              f"**Hook idea (model-written, not a quote):** {c.get('hook_idea', '')}",
              f"**Context needed:** {c.get('context_needed', '')}",
              f"**CTA idea:** {c.get('cta', '')}",
              f"**Scores:** {c.get('scores')}", f"**Why:** {c.get('rationale', '')}",
              "", "> " + c["transcript"]]
    out = proj / "reports" / "clip_candidates.md"
    out.write_text("\n".join(L))
    return out
