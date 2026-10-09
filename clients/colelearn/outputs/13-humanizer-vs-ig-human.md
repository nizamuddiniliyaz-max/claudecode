# Humanizer head-to-head — @colelearn (test run)

Input: a deliberately AI-sounding caption.
> In today's fast-paced fitness landscape, it's important to note that HYROX success isn't about training more — it's about training smarter. By leveraging strategic running sessions, athletes can unlock their full potential and elevate their race-day performance to new heights. Remember: consistency is key, recovery is crucial, and mindset is everything.

| Version | Text | detect.py human score |
|---|---|---|
| Original | (above) | 20.2 FLAGGED |
| Jake `humanize.py` (script) | In today's fast-paced fitness market, it's important to note that HYROX success isn't about training more, it's about training smarter. By using strategic running sessions, athletes can get their full potential and improve their race-day performance to new heights. Remember: consistency is key, recovery is important, and mindset is everything. | 37.8 FLAGGED |
| blader `humanizer` (LLM rewrite, no new facts) | You run 8K in every HYROX, so that's where I'd spend your training time. Run most days and keep the easy ones easy. Recovery counts as training. So does getting your head right before the start line.  | 40.1   FLAGGED |

## Findings
- Jake's script only swaps words. It kept "it's not X, it's Y", "to new heights" and the triad, and produced "get their full potential". It's a pre-filter, not a humanizer.
- blader's humanizer caught the structural tells (not-X-but-Y, triad, staged "Remember:"). My first rewrite still had a not-X-but-Y contrast ("More training won't fix it. Smarter running will."), which its own checklist flags.
- **Fabrication risk found:** an intermediate rewrite added "I raced Elite 15 in Melbourne off this". That scored higher (72.6) but it's an invented claim. The humanizer's rule ("do not add a fact") is right. A higher detector score is not worth a made-up fact.
- **Best combo:** blader `humanizer` to rewrite, then Jake `detect.py` as the scoreboard.
