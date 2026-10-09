# Content Machine — Skill Scorecard

Installed: 39 skills in `.claude/skills/` (sources + commits in `licenses/SOURCES.txt`, all MIT).

Legend: ✅ pass · ⚠️ works with caveat · ❌ fail · ⏳ not tested yet

## Round 1 — Install & tool checks (2026-10-09)

| Skill | Source | Check | Result | Notes |
|---|---|---|---|---|
| all 39 | — | SKILL.md frontmatter (name + description) | ✅ | All valid |
| ig-reel | Jake | `hookscore.py` ranks 3 hooks | ✅ | Correctly ranked the weak "5 tips" hook last (55) |
| ig-reel | Jake | `beats.py` timed beat sheet | ✅ | Flagged under-length, detected the hook→ending loop |
| ig-caption | Jake | `caption.py` lint | ✅ | Caught 6 hashtags (cap 5) and a 183-char first line |
| ig-human | Jake | `humanize.py` | ⚠️ | Mechanical first pass only. Produced a grammar bug ("a plethora of" → "a lots of"); left "delving" / "new heights". Needs the LLM rewrite + `humanizer` after it |
| ig-human | Jake | `detect.py` | ✅ | AI text scored 26.8 (FLAGGED), human script 52.7 (REVIEW) |
| ig-viral | Jake | `swipe.py` ranking | ✅ | Outlier multiples, formula names, and top-vs-bottom summary all correct |
| last30days | mvanhorn | `--diagnose` | ✅ | Engine ready on Python 3.13 |
| last30days | mvanhorn | live research | ❌ env | Cloud network policy blocks reddit.com / news.ycombinator.com (403). Not a skill bug |

## Round 2 — Per-skill output tests (with a test account)

| # | Skill | Prompt used | Runs? | Follows own rules? | Fits the account? | Hands off? | Score /10 |
|---|---|---|---|---|---|---|---|
| | | | ⏳ | | | | |

## Known issues / to-do
- Jake's skills save to `~/.claude/instagram/` (one global voice). For multiple clients, the `/ig` router must point them at `clients/<name>/` instead.
- last30days needs network access (Reddit, HN, web) + optional ScrapeCreators key for IG/TikTok.
