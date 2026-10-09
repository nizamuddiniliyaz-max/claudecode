#!/usr/bin/env python3
"""Sanity check that needs no footage: builds a fake 16:9 video + transcript and renders 6 sample reels
(one per caption style, each with different motion graphics).

    python selftest.py            # then look in selftest/out/
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "selftest")
os.makedirs(D, exist_ok=True)

SENT = [
    "Every team has a hierarchy whether you draw it or not.",
    "The question is whether the hierarchy helps people or blocks them.",
    "At the top you need vision and clear direction.",
    "In the middle you need managers who translate strategy into action.",
    "At the base you have the people doing the real work every single day.",
    "When authority is unclear nobody knows who decides.",
    "Good leaders give authority and keep accountability close.",
    "That is how a flat team still moves fast.",
    "Eighty percent of delays come from unclear ownership.",
    "So draw the org chart and then fix the gaps.",
    "Promotion should follow responsibility and not just seniority.",
    "Build the ladder one step at a time and everyone climbs.",
]


def make_transcript():
    words, t = [], 1.0
    for s in SENT:
        for w in s.split():
            dur = 0.17 + 0.035 * len(w)
            words.append(dict(w=w, start=round(t, 3), end=round(t + dur, 3)))
            t += dur + 0.04
        t += 1.1  # long pause between sentences -> should be trimmed
    return words, t


def main():
    words, total = make_transcript()
    dur = int(total) + 2
    src = os.path.join(D, "fake_source.mp4")
    if not os.path.exists(src):
        subprocess.check_call([
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", f"testsrc2=s=1920x1080:r=30:d={dur}",
            "-f", "lavfi", "-i", f"sine=f=220:d={dur}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", src])
    with open(os.path.join(D, "transcript.json"), "w") as f:
        json.dump(dict(words=words), f)
    # sentence boundaries -> clips
    def at(word_idx):
        return words[word_idx]["start"]
    idx, bounds = 0, []
    for s in SENT:
        n = len(s.split())
        bounds.append((idx, idx + n - 1))
        idx += n
    S = lambda i: dict(start=round(words[bounds[i][0]]["start"] - 0.2, 2), end=round(words[bounds[i][1]]["end"] + 0.3, 2))
    # one rich clip spanning several sentences per style
    def span(a, b):
        return dict(start=round(words[bounds[a][0]]["start"] - 0.2, 2), end=round(words[bounds[b][1]]["end"] + 0.3, 2))
    wt = lambda i: round(words[i]["start"], 2)
    clips = [
        dict(id=1, caption_style="impact", theme="midnight", hook="Your team already has a hierarchy",
             tag="Leadership", **span(0, 2),
             graphics=[dict(type="pyramid", at=wt(bounds[2][0]), dur=4.5, labels=["Vision", "Managers", "Doers"],
                            highlight=0, title="The hierarchy"),
                       dict(type="emoji", char="👑", at=wt(bounds[0][0] + 3), dur=1.8, x=0.82, y=0.27)]),
        dict(id=2, caption_style="boxed", theme="violet", hook="Who actually decides here?",
             tag="Watch this", **span(3, 5),
             graphics=[dict(type="tree", at=wt(bounds[4][0]), dur=6, title="Org chart",
                            tree={"label": "CEO", "children": [
                                {"label": "Ops", "children": ["Team A", "Team B"]},
                                {"label": "Sales", "children": ["Team C"]}]},
                            highlight=["CEO", "Ops"])]),
        dict(id=3, caption_style="editorial", theme="ember", hook="Authority without accountability fails",
             emphasis=["accountability", "authority", "hierarchy"], **span(5, 7),
             graphics=[dict(type="keyword", text="Accountability", sub="keep it close", at=wt(bounds[6][0] + 4), dur=2.2),
                       dict(type="emoji", char="🔥", at=wt(bounds[7][0] + 2), dur=1.6, x=0.2, y=0.28)]),
        dict(id=4, caption_style="marker", theme="forest", hook="80% of delays are one thing", **span(8, 9),
             graphics=[dict(type="stat", value=80, suffix="%", label="of delays: unclear ownership", at=wt(bounds[8][0]), dur=3.2)]),
        dict(id=5, caption_style="stack", theme="midnight", hook="Promotion is not a reward", **span(10, 11),
             graphics=[dict(type="steps", at=wt(bounds[11][0]), dur=5, labels=["Learn", "Own", "Lead", "Scale"],
                            title="The ladder")]),
        dict(id=6, caption_style="glow", theme="violet", hook="Flat teams still need structure",
             layout="fit", **span(6, 7),
             graphics=[dict(type="keyword", text="Structure", at=wt(bounds[7][0] + 1), dur=2.0)]),
    ]
    cfg = dict(source="fake_source.mp4", transcript="transcript.json", clips=clips)
    with open(os.path.join(D, "clips.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print("fake video + transcript + clips.json written to", D)
    r = subprocess.call([sys.executable, os.path.join(HERE, "02_render.py"), os.path.join(D, "clips.json"),
                         "--no-face"] + sys.argv[1:])
    sys.exit(r)


if __name__ == "__main__":
    main()
