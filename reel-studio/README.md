# reel-studio

Turn one long horizontal video into 10-15 vertical reels, **entirely on your own computer**:
no cloud, no subscription, no stock images. Silence/pauses are trimmed, captions are animated
word by word (6 different styles to test), and motion graphics are drawn in code.

## What it does

| Step | How |
|---|---|
| Transcribe | `faster-whisper` (local) -> word-level timestamps |
| Pick reels + hooks | Claude reads `transcript.txt` and writes `clips.json` (you paste the text, not the video) |
| Trim pauses | pauses longer than 0.35 s are cut out; subtle alternate punch-in hides the jump cuts |
| 9:16 reframe | `crop` = centred on the speaker's face (needs OpenCV), or `fit` = whole frame over a blurred backdrop |
| Captions | 6 styles, each a different font + animation (see below) |
| Motion graphics | hook title card, pyramid, org tree, steps/ladder, keyword pop, stat counter, emoji pop, progress bar |
| Audio | loudness-normalised; optional background music that ducks under speech |

### Caption styles (`caption_style`)
| name | font | look |
|---|---|---|
| `impact` | Anton | chunky white caps, black outline, live word turns yellow and pops |
| `boxed` | Poppins Bold | lowercase, live word sits on a coloured box that jumps along |
| `editorial` | Playfair Display Italic | words fade in; key words go bigger, gold, underlined |
| `marker` | Permanent Marker | tilted hand-drawn caps, rotating colours, scribble under the live word |
| `stack` | Bebas Neue | huge two-line stack, staggered left/right, second line smaller + red |
| `glow` | Montserrat | whole phrase dim, the spoken word lights up with a soft glow |

Captions sit at ~61 % of the screen height (below centre, clear of the Instagram UI). Graphics that
take over the screen sit above them.

## Install (once)

1. **FFmpeg** - macOS: `brew install ffmpeg` - Windows: `winget install ffmpeg`
2. **Python 3.10+**, then in this folder:
   ```
   pip install -r requirements.txt
   ```
   (`opencv-python-headless` is optional; without it the crop is centred instead of following the face.)

## Check it works (no footage needed)

```
python selftest.py --preset ultrafast --jobs 2
```
Renders 6 sample reels into `selftest/out/`. Ready-made small copies are in `demo/`.

## Real run

```
python 01_transcribe.py "/path/to/video1669769194.mp4"      # -> work/transcript.txt + transcript.json
```
Paste the contents of `work/transcript.txt` to Claude. It returns a `clips.json`. Save it in `work/`, then:

```
python 02_render.py work/clips.json --preview 12   # fast look at the first 12 s of each reel
python 02_render.py work/clips.json --jobs 3       # full render (3 reels in parallel)
python 02_render.py work/clips.json --only 02,05   # re-do specific reels
```
Reels land in `work/out/`. Roughly 15-20 frames/s per reel on a laptop CPU, so a 60 s reel takes 2-4 minutes.

Useful flags: `--no-face` (centre crop), `--crf 20` (smaller files), `--no-loudnorm`.

## clips.json

See `clips.example.json`. Times are **seconds in the original video**. Per clip:

```json
{ "id": 1, "start": 312.4, "end": 371.0,
  "hook": "Your team already has a hierarchy", "tag": "Leadership",
  "caption_style": "impact", "theme": "midnight", "layout": "crop",
  "graphics": [ ... ] }
```
Graphic types: `pyramid`, `tree`, `steps`, `keyword`, `stat`, `emoji` (details in the example file).
Graphics that would overlap another graphic or the hook card are shifted automatically.
Optional per clip: `"music": {"file": "bgm.mp3", "gain_db": -20}`, `"crop_x": 0.42`, `"max_gap": 0.35`,
`"punch_in": 1.07`, `"caption_y": 1170`, `"progress_bar": false`.

## Known limits (be aware)

- Face-centred crop (`crop` layout) is **untested on real footage** - only on synthetic video. If a
  speaker is off-centre, set `"crop_x"` (0..1) on that clip or use `"layout": "fit"`.
- A 16:9 Zoom frame cropped to 9:16 is upscaled ~1.8x, so it looks softer than the original.
- Music is optional and never chosen automatically; Claude suggests where it fits, you supply the file.
- Emoji come from the bundled Noto Color Emoji font; any standard emoji character works.

## Licenses

Code: yours to use. Fonts: SIL OFL / Apache (licenses in `fonts/`). All bundled fonts allow commercial use.
