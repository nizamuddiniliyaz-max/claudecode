# @colelearn — /ig-comment, /ig-reply, /ig-repurpose, /ig-audit, /ig-viral (test run)

## 08 /ig-comment
Input (paraphrased, public): Hunter McIntyre's video "Hunter McIntyre & Cole Learn Attempt HYROX Doubles
World Record in Las Vegas". In real use, paste the actual post text.
```
[6 · Receipt]
Doubles is a different race. You run every k at your partner's worst pace,
so we trained the handoffs more than the stations.        ⚠️ {{Cole to confirm, invented detail}}
[2 · Missing case]
Agree the sled is where people panic. The part I'd add: the first 100 m after
it decides your next split, not the push itself.
Post the second. It's true for anyone and doesn't need a fact we haven't checked.
```
detect.py: both 62.0 REVIEW. Every short comment got the identical score, so the detector can't judge text this short.

## 09 /ig-reply — SYNTHETIC comments (no real thread available)
```
REPLIES · 8 comments · 3 KEYWORD, 1 LEAD, 1 SUBSTANCE, 1 QUESTION, 1 SUPPORT, 1 NOISE
KEYWORD (3)   @a, @b, @c commented S60 → reply "Sent, check your DMs" + deliver link by hand
LEAD          @gymowner_on: "my members all die on the sled run"
              → "Same story everywhere. Have them do sled + 400 m once a week and keep the
                 first 100 m short and quick. Happy to share how we set it up."
SUBSTANCE     @runcoach: "8K isn't much for runners, the issue is the stations"
              → "Fair for pure runners. For most gym-goers it's the opposite. They're strong
                 and the 8K is what breaks them."
QUESTION      @newbie: "how many weeks out should I start training?"  → REPLY WITH A REEL (#16)
SUPPORT       "🔥🔥" → like + "Appreciate it"
NOISE         "DM me for collab 💰" → nothing
```

## 10 /ig-repurpose
Source: Rox Lyfe podcast "From Homeless to Elite 15" (Jan 2026). **Only the episode description was
reachable, not the 40+ min transcript.**
```
FOUND  2 claims, 2 numbers, 1 story, 1 mechanism, 0 mistakes, 0 quotable lines
VERDICT  THIN. Fewer than 4 strong extracts. Need the transcript or audio before building a week.
Possible from what we have:
  REEL  #20 Permission   "You don't need huge volume at the top of HYROX"
  REEL  #21 Mid-Sentence "...and I didn't know if I'd wake up some days." (Cole's own words, needs his OK)
```
Skill behaved correctly: it flagged the source as thin instead of padding.

## 11 /ig-audit — SYNTHETIC insights (to test the maths only)
```
AUDIT · 8 posts · median views 10,450
TOP 3 BY OUTLIER MULTIPLE
  8.4x  WR 49:13 splits        78% non-follower  hold@3s 69%  46 sends / 1k reach
  5.0x  Homeless to Elite 15   74% non-follower  hold@3s 62%  82 sends / 1k reach  ← most sent
  3.9x  Stop adding sessions   71% non-follower  hold@3s 64%  35 sends / 1k reach
BOTTOM 3
  0.6x  Race-week vlog / 0.4x Sponsor post / 0.4x Gym day dump   hold@3s 30–41%
FINDING  The top three all hold 62%+ at 3s; the bottom three hold 41% or less. It's the hook,
         not the topic. Only 8 posts, so low confidence.
```
Needs real Insights screenshots for a real audit.

## 12 /ig-viral
**Blocked in this environment.** It needs a logged-in browser (Claude desktop / Chrome extension) or
pasted reel data. The ranking tool (`swipe.py`) passed with sample data in Round 1.
For Cole: collect 6–12 HYROX accounts × ~12 reels each, paste the TSV, and it builds the swipe file.
