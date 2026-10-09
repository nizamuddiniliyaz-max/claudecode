# /ig-reel — @zaryskicalvin (test run)

Idea: "Your brick run is too fast. Run it at 95% of your fresh 10K pace."
Source of the 95% figure: Cal's own blog post "To BRICK or Not to BRICK" (criticalspeed.com).

```
HOOKS (scored by hookscore.py)
  83.0  STRONG  #2  Negative Command  "Stop running bricks all-out. Run them at 95% of your 10K pace."
  80.8  STRONG  #2  (tightened)       "Run your brick at 95% of 10K pace. Not all-out."   ← use this
  47.1  WEAK    #8  Insider Leak      "I've coached triathletes for 30 years. Most of them run their bricks too hard."
  26.9  WEAK    #7  Wrong Way         "Your brick run is too fast, and it is costing you the race."
```

## Iterations (beats.py caught real problems)
- v1: 39.8s, hook 4.5s long, 7 beats over 4s. **Failed.**
- v2: 24.8s, but the short hook lost its number ("Beats 1-3 have nothing concrete").
- v3: hook carries the number again (95%, 10K). Use v3.

## Script (v3)
```
Run your brick at 95% of 10K pace. Not all-out.
Most age-groupers hammer it off the bike.
Then they blow up on race day.
Athletes run best off the bike at 95% of fresh 10K pace.
10K at 5:00 per K? Brick at about 5:15.
Hold it 15 to 20 minutes.
Easy first two K. Then settle.
Feels too easy. That's the point.
Save this. Stop running bricks all-out.
```

## On-screen cards
| Time | Card |
|---|---|
| 0:00 | BRICK = 95% OF 10K PACE |
| 0:05 | NOT ALL-OUT |
| 0:11 | 5:00/K → 5:15/K |
| 0:16 | 15–20 MIN |
| 0:21 | SAVE THIS |

```
REEL READY
hook:       #2 Negative Command (tightened), scored 80.8 STRONG
length:     ~26s at 160 wpm
loop:       last beat echoes "bricks / all-out"
humanizer:  detect.py 67.3 REVIEW (weakest: burstiness)
caption:    run /ig-caption next
```

## Fact-check flags
- "Athletes run best at 95%": the blog says *most athletes reported good runs* at 95% in a
  simulated Olympic-distance test. Cal should confirm he's happy with the simplified wording.
- 15–20 min duration and the 5:00 → 5:15 example are my illustration (5:00 ÷ 0.95 = 5:16). Confirm.
