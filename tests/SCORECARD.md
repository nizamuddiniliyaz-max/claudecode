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

## Round 2 — Per-skill tests on @colelearn + @zaryskicalvin (2026-10-09)

Test conditions: Instagram, Linktree and most article sites are blocked from this cloud
environment, so profiles/voices were built from web-search facts only (no real captions).
Outputs: `clients/<account>/outputs/`. Score = usefulness for the content machine (/10).

| # | Skill | Source | Ran on | Result | Score | Notes |
|---|---|---|---|---|---|---|
| 1 | brand-profile | SMS | both | ✅ | 9 | Best foundation file. Forces proof, guardrails, AI policy |
| 2 | voice-builder | SMS | both | ✅ refused | 8 | Correctly refused without real samples. Needs 3+ captions |
| 3 | ig-profile | Jake | both | ⚠️ | 7 | Good rubric; 56–94 pts unscorable without a screenshot |
| 4 | ig-reel | Jake | both | ✅ | 10 | Hook scorer + beat timer caught real problems (4.5s hook, 7 slow beats) |
| 5 | ig-caption | Jake | both | ✅ | 10 | Linter caught missing keywords + no number; v2 READY |
| 6 | ig-carousel | Jake | both | ⚠️ | 8 | Great copy rules; no renderer included (built one with Playwright) |
| 7 | ig-story | Jake | both | ✅ | 8 | Clear frame + sticker logic |
| 8 | ig-plan | Jake | both | ✅ | 8 | Good weekly mix; engagement handles need verifying |
| 9 | ig-dm | Jake | both | ✅ | 9 | Strong anti-spam rules; collab pitch template is useful |
| 10 | ig-comment | Jake | both | ✅ | 8 | 9 comment types work; tempts invented "receipts" (flagged) |
| 11 | ig-reply | Jake | synthetic | ✅ | 8 | Triage buckets + reply-with-Reel idea are excellent |
| 12 | ig-repurpose | Jake | both | ✅ | 8 | Correctly flagged thin sources instead of padding |
| 13 | ig-audit | Jake | synthetic | ✅ | 8 | Maths verified; needs real Insights |
| 14 | ig-viral | Jake | — | ❌ env | — | Needs browser/pasted data. Tool passed Round 1 |
| 15 | ig-human | Jake | both | ⚠️ | 5 | detect.py useful as a scoreboard; humanize.py weak, adds grammar errors; short text all scores 62.0 |
| 16 | humanizer | blader | Cole | ✅ | 9 | Catches structural tells; strict "no new facts" rule |
| 17 | last30days | mvanhorn | — | ❌ env | — | Engine OK; Reddit/HN/web blocked by network policy |
| 18 | hook-writer | SMS | both | ✅ | 8 | More variety than ig-reel; needs a fact-check pass |
| 19 | caption-writer | SMS | both | ✅ | 7 | Good for picking an angle; ig-caption better for finishing |
| 20 | short-form-video-script | SMS | both | ✅ | 6 | Duplicates ig-reel for IG; keep for cross-platform |
| 21 | tiktok-script | SMS | Cole | ✅ | 8 | Shot/on-screen/spoken/sound table is production-ready |
| 22 | youtube-shorts | SMS | both | ✅ | 7 | Adds searchable titles; otherwise same script |
| 23 | linkedin-post-writer | SMS | Cal | ✅ | 8 | Good fit for coaches/business owners |
| 24 | x-growth | SMS | Cole | ✅ | 6 | Fine; low priority for these niches |
| 25 | cross-platform-repurposing | SMS | both | ✅ | 8 | Clean one-idea-to-every-platform map |
| 26 | viral-reverse-engineering | SMS | both | ✅ refused | 7 | Correctly stopped without observable data |
| 27 | capcut | SMS | both | ✅ | 7 | EDITS checklist + music-licensing warning (important for sponsored athletes) |
| 28 | captions-and-clipping | SMS | both | ⚠️ | 7 | Good podcast→Shorts plan; needs the audio file |
| 29 | social-seo | SMS | both | ✅ | 6 | ~70% overlap with instagram-seo |
| 30 | instagram-seo | SMS | both | ✅ | 8 | MATCH framework is practical |
| 31 | instagram-growth | SMS | both | ✅ | 8 | Diagnoses the stuck stage before prescribing |
| 32 | batch-content-plan | SMS | both | ✅ | 7 | Monthly version of ig-plan. Pick one |
| 33 | social | Corey | both | ⚠️ | 5 | Mostly duplicates SMS + Jake |
| 34 | content-strategy | Corey | both | ✅ | 8 | Searchable-vs-shareable split is the best strategy lens |
| 35 | ads | Corey | both | ✅ | 8 | Sensible Meta setup + kill rules |
| 36 | ad-creative | Corey | both | ✅ | 8 | Good variations; bans AI tells |
| 37 | influencer-marketing | Corey | both | ✅ | 7 | Useful flipped into an ambassador program |
| 38 | image | Corey | both | ⚠️ | 5 | Suggests AI imagery; ignores brand-profile guardrails |
| 39 | video | Corey | both | ⚠️ | 5 | Avatar-heavy; Hyperframes part is useful |

### Cross-cutting findings
1. **Fabrication pressure is the #1 risk.** Hooks/comments/rewrites kept "needing" a number or a
   story. 6 invented details were caught and flagged (e.g., "lose 3 minutes in the Roxzone",
   "50-something"). Every client must sign off on facts.
2. **Hook scorer bias:** Jake's hookscore.py ranked Cole's strongest story hook last (47). Use it to
   catch weak hooks, not to veto narrative ones.
3. **Corey's skills read `.agents/product-marketing.md`**, not `brand-profile.md`. The router must bridge this.
4. **Jake's skills use one global `~/.claude/instagram/` folder.** Multi-client needs the router to
   point them at `clients/<name>/`.
5. **Duplicates to resolve in the router:** ig-plan vs batch-content-plan; ig-reel vs
   short-form-video-script; social-seo vs instagram-seo; Corey `social` vs everything.

## Known issues / to-do
- Jake's skills save to `~/.claude/instagram/` (one global voice). For multiple clients, the `/ig` router must point them at `clients/<name>/` instead.
- last30days needs network access (Reddit, HN, web) + optional ScrapeCreators key for IG/TikTok.
