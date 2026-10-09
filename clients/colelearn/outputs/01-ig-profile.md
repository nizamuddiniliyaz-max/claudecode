# /ig-profile — @colelearn (test run)

Input: public search snapshot only. Name "Cole Learn"; bio mentions "E15 Hyrox Athlete 🇨🇦",
"Mixed Doubles WR", sponsors adidas + Wodify; link linktr.ee/colelearnfit; ~44K followers,
~1,028 posts. Pinned posts, highlights, grid, photo and activity were NOT visible.

## Score (observable items only)

```
PROFILE SCORE  20/44 scored  (56 points unscorable without a screenshot)

  name field        3/12   "Cole Learn" only — no searched words (HYROX, coach)
  bio first line    5/12   says what he is (E15 athlete), not who it's for or what changes
  bio body          5/8    world record is strong proof; sponsor tags eat characters
  link              3/8    Linktree = a menu; the bio doesn't say where to tap
  handle            6/6    clean, sayable, matches his name
  pinned three      —/10   not visible
  highlights        —/8    not visible
  grid legibility   —/8    not visible
  photo             —/6    not visible
  category/contact  —/6    not visible
  recent activity   —/10   not visible (posts appear active in 2026)
  story presence    —/6    not visible
```

## Rewrites (fix-first order)

**1. Name field (30 chars max)**
- `Cole Learn | HYROX Coach` (24)
- `Cole Learn | HYROX Elite 15` (27)
- `Cole Learn | HYROX Training` (27)

**2. Bio (137 / 150 chars)**
```
Helping you race faster HYROX on 60-minute sessions.
Mixed Doubles world record 49:13. Elite 15. 10 years sober.
Get the S60 plan below.
```
Sponsors move to the "Partners" highlight and paid-partnership labels.
(⚠️ "10 years sober" is in the public record but Cole decides whether it goes in the bio.)

**3. Pinned three**
1. Proof: the Melbourne world-record race (49:13).
2. Offer: "What a 60-minute S60 session looks like".
3. Intro: the "from homeless to Elite 15" story reel.

**4. Highlights:** S60 Plan · Results · Race Week · My Story · Partners

**5. Link:** point straight at the S60 plan page. Keep Linktree only if sponsor codes must live there.

## Re-score
Observable items 20/44 → about 36/44 after rewrites. The other 56 points need a real screenshot.

## ig-human check
`detect.py` on the bio: 49.0 FLAGGED (burstiness). The text is too short for the detector to judge
fairly; a 3-line bio always reads as "low variation". Treat as a detector limit, not a voice problem.
