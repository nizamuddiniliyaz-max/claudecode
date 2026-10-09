"""Research with provenance. Only records data that was actually retrieved.

Milestone 1 sources: YouTube Data API (official, needs YOUTUBE_API_KEY) and manual notes.
Reddit/Trends are deliberately not wired: API terms not yet reviewed; pytrends is archived.
"""
import datetime as dt
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

LIMITS = [
    "Public view/like counts do not show retention or watch time.",
    "Search results are a snapshot, not a trend measurement.",
    "Topic suggestions are model judgment unless a metric is attached.",
]


def youtube_search(query: str, key: str, n: int = 10) -> list[dict]:
    today = dt.date.today().isoformat()
    q = urllib.parse.urlencode({"part": "snippet", "q": query, "type": "video", "maxResults": n, "key": key})
    with urllib.request.urlopen(f"https://www.googleapis.com/youtube/v3/search?{q}", timeout=30) as r:
        items = json.load(r).get("items", [])
    ids = ",".join(i["id"]["videoId"] for i in items)
    stats = {}
    if ids:
        q = urllib.parse.urlencode({"part": "statistics", "id": ids, "key": key})
        with urllib.request.urlopen(f"https://www.googleapis.com/youtube/v3/videos?{q}", timeout=30) as r:
            stats = {v["id"]: v.get("statistics", {}) for v in json.load(r).get("items", [])}
    return [{
        "title": i["snippet"]["title"], "channel": i["snippet"]["channelTitle"],
        "published": i["snippet"]["publishedAt"], "accessed": today, "query": query,
        "url": f"https://www.youtube.com/watch?v={i['id']['videoId']}",
        "metrics": {k: int(v) for k, v in stats.get(i["id"]["videoId"], {}).items()
                    if k in ("viewCount", "likeCount", "commentCount")},
        "metrics_source": "YouTube Data API v3",
    } for i in items]


def run(proj: Path, queries: list[str]) -> Path:
    key = os.environ.get("YOUTUBE_API_KEY")
    topics, errors = [], []
    for q in queries:
        entry = {"query": q, "sources": [], "confidence": "none"}
        if key:
            try:
                entry["sources"] = youtube_search(q, key)
                entry["confidence"] = "low-medium: public metrics only"
            except Exception as e:  # keep going; record the failure honestly
                errors.append(f"{q}: {e}")
        topics.append(entry)
    notes = Path(proj) / "research" / "manual_notes.md"
    out = Path(proj) / "research" / "research.json"
    out.write_text(json.dumps({
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "sent_off_device": "Search query strings only" if key else "Nothing (no YOUTUBE_API_KEY set)",
        "limits": LIMITS, "errors": errors, "topics": topics,
        "manual_notes": notes.read_text() if notes.exists() else None,
    }, indent=1))
    return out
