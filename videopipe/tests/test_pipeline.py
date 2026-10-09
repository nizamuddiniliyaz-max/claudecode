import json
import subprocess

import pytest

from videopipe import analyze, candidates, project, report

WORDS = []
def _add(text, t, speaker, dur=0.3, gap=0.05):
    for w in text.split():
        WORDS.append({"w": w, "start": round(t, 2), "end": round(t + dur, 2), "speaker": speaker, "score": 0.95})
        t += dur + gap
    return t

t = _add("So what should I do in the first ten minutes of a Hyrox race?", 0, "HOST")
t = _add("um", t + 0.2, "COACH")
t = _add("Go slower than feels right. Hold zone two pace and let the first wall ball set come easy.", t + 1.5, "COACH")
t = _add("Most people blow up on the sled push because they started too hard.", t, "COACH")


@pytest.fixture
def proj(tmp_path):
    v = tmp_path / "talk.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc=d=2:s=160x90:r=10",
                    "-f", "lavfi", "-i", "sine=d=2", "-shortest", str(v)], check=True)
    p = project.init_project(v, tmp_path / "VideoProjects")
    (p / "transcript" / "transcript.json").write_text(json.dumps({"language": "en", "words": WORDS, "segments": []}))
    return p


def test_init_preserves_source_and_records_metadata(proj, tmp_path):
    meta = json.loads((proj / "metadata.json").read_text())
    assert meta["sha256"] == project.sha256(tmp_path / "talk.mp4")
    assert meta["width"] == 160 and meta["audio_tracks"] == 1 and meta["fps"] == 10
    assert not (proj / "source" / "talk.mp4").stat().st_mode & 0o200  # read-only
    for d in project.SUBDIRS:
        assert (proj / d).is_dir()


def test_cut_proposals_flag_filler_and_pause_but_never_delete(proj):
    out = json.loads(analyze.run(proj).read_text())
    kinds = {p["type"] for p in out["proposals"]}
    assert {"filler", "pause"} <= kinds and out["status"] == "proposal_only"


def test_locate_and_verify_reject_fabricated_quotes():
    good = {"start_text": "Go slower than feels right", "end_text": "come easy", "topic": "pacing"}
    v = candidates.verify(good, WORDS)
    assert v and v["start"] < v["end"] and "COACH" in v["speakers"]
    bad = {"start_text": "Never start fast", "end_text": "come easy"}
    assert candidates.verify(bad, WORDS) is None
    reversed_ = {"start_text": "come easy", "end_text": "Go slower than feels right"}
    assert candidates.verify(reversed_, WORDS) is None


def test_weighted_score():
    assert candidates.weighted(dict.fromkeys(
        ["audience_match", "answer_completeness", "hook_clarity", "standalone", "specificity"], 8)) == 8.0


def test_end_to_end_with_fake_llm_drops_unverified(proj):
    fake = json.dumps({"clips": [
        {"topic": "pacing", "question_text": "first ten minutes?",
         "start_text": "So what should I do", "end_text": "started too hard",
         "scores": dict(audience_match=5, answer_completeness=9, hook_clarity=7, standalone=8, specificity=8)},
        {"topic": "made up", "start_text": "This was never said", "end_text": "at all", "scores": {}},
    ]})
    out = json.loads(candidates.run(proj, llm=lambda s, u: fake).read_text())
    assert len(out["clips"]) == 1 and out["dropped_unverified"] >= 1
    assert out["clips"][0]["clip_id"] == "C01" and out["status"] == "needs_human_review"
    md = report.run(proj).read_text()
    assert "C01" in md and "not a quote" in md
