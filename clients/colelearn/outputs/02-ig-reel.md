# /ig-reel — @colelearn (test run)

Idea: "You don't need two sessions a day to race elite HYROX."

```
HOOKS (scored by hookscore.py)
  87.0  STRONG  #2  Negative Command  "Stop adding sessions. Fix your running instead."
                                      on screen: STOP ADDING SESSIONS
  77.8  STRONG  #20 Permission        "You do not need two sessions a day to race elite HYROX."
                                      on screen: NO TWO-A-DAYS NEEDED
  39.3  WEAK    #6  The Receipt       "I set a HYROX world record on one session a day. Here's the week."
                                      DROPPED: also an unverified claim about his training
```

## Script (shoot #2)
```
Stop adding sessions. Fix your running instead.
Most people training for HYROX think they need more volume.
I race Elite 15. I don't believe in huge volume.
You run 8K in a HYROX. That's where the time is.
Run easy most days. One hard run a week.
Practise running straight off the sled and the wall balls.
Sleep. Mobility. Show up again tomorrow.
Want my week? Comment S60.
Stop adding sessions. Fix your running.
```

## On-screen cards
| Time | Card |
|---|---|
| 0:00 | STOP ADDING SESSIONS |
| 0:05 | 8K OF RUNNING |
| 0:10 | EASY MOST DAYS |
| 0:14 | RUN OFF THE SLED |
| 0:18 | SLEEP. MOBILITY. REPEAT. |
| 0:21 | COMMENT "S60" |

```
REEL READY
hook:       #2 Negative Command, scored 87.0 STRONG
length:     ~25.4s at 175 wpm (4.6s under the 30s target, kept short on purpose)
loop:       last beat echoes "adding / fix / running"
humanizer:  detect.py 62.7 REVIEW (weakest: specificity)
caption:    run /ig-caption next
```

## Fact-check flags (must confirm with Cole)
- "I don't believe in huge volume": based on his Rox Lyfe podcast description. Confirm wording.
- Draft v1 said "That's how I got to a world record" and "I don't do two-a-days". **Removed**: not verified.
- Easy-run / one hard run split is a generic recommendation. Replace with his actual week.
