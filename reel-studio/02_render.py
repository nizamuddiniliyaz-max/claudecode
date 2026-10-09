#!/usr/bin/env python3
"""Step 2 - render the reels described in a clips.json (everything runs locally).

    python 02_render.py clips.json                 # all reels
    python 02_render.py clips.json --only 01,04    # just these
    python 02_render.py clips.json --preview 12    # first 12 s of each (fast check)
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time

from PIL import Image

from reelkit import captions as cap
from reelkit import graphics as gfx
from reelkit.cut import (CutMap, build_graph, filter_flag, keep_intervals, probe, remap_words)
from reelkit.reframe import face_center_fraction
from reelkit.util import FPS, H, W, THEMES, theme

STYLE_ORDER = ["impact", "boxed", "editorial", "marker", "stack", "glow"]
THEME_ORDER = ["midnight", "ember", "forest", "violet"]


def resolve_overlaps(events, hook, total, cid):
    """Graphics share the same screen area: never let two (or the hook) show at once."""
    out, busy_until = [], (hook.t0 + hook.dur + 0.1) if hook else 0.0
    for e in sorted(events, key=lambda e: e.t0):
        if isinstance(e, gfx.EmojiPop):
            out.append(e)
            continue
        if e.t0 < busy_until:
            print(f"[{cid}]   graphic at {e.t0:.1f}s collides with another; moved to {busy_until:.1f}s")
            e.t0 = busy_until
        if e.t0 + e.dur > total - 0.05:
            e.dur = total - 0.05 - e.t0
        if e.dur < 0.8:
            print(f"[{cid}]   graphic dropped (no room left)")
            continue
        busy_until = e.t0 + e.dur + 0.15
        out.append(e)
    return out


def render_clip(cfg, clip, idx, args, ffmpeg, flag):
    src = cfg["source"]
    sw, sh = probe(src)
    d = {**cfg.get("defaults", {}), **clip}
    cid = str(d.get("id", idx + 1)).zfill(2)
    style = d.get("caption_style") or STYLE_ORDER[idx % len(STYLE_ORDER)]
    th = theme(d.get("theme") or THEME_ORDER[idx % len(THEME_ORDER)])
    start, end = float(d["start"]), float(d["end"])
    words = [w for w in cfg["_words"] if w["end"] > start and w["start"] < end]
    if not words:
        print(f"[{cid}] no words in range, skipped")
        return
    ivs = keep_intervals(words, start, end, d.get("max_gap", 0.35), d.get("pad_pre", 0.06),
                         d.get("pad_post", 0.12))
    cmap = CutMap(ivs)
    total = cmap.total
    if args.preview:
        total = min(total, args.preview)
    base = ivs[0][0]
    win_end = ivs[-1][1]
    layout = d.get("layout", "crop")
    d.setdefault("caption_y", 1430 if layout == "fit" else 1170)
    crop_x = d.get("crop_x")
    if layout == "crop" and crop_x is None and not args.no_face:
        crop_x = face_center_fraction(src, start, min(end, start + 120))
        print(f"[{cid}] speaker x-position: {crop_x if crop_x is not None else 'centre (no face found / no OpenCV)'}")
    out_words = remap_words(cfg["_words"], cmap, start, end)

    emphasis = list(d.get("emphasis", []))
    for g in d.get("graphics", []):
        if g["type"] == "keyword":
            emphasis += g["text"].split()
    track = cap.CaptionTrack(out_words, style, emphasis, cy=d.get("caption_y", 1170))
    events = gfx.build_events(d.get("graphics", []), th, cmap, cmap.total)
    hook = gfx.HookCard(d["hook"], th, tag=d.get("tag", ""), dur=d.get("hook_dur", 2.9)) if d.get("hook") else None
    top_events = ([hook] if hook else [])
    events = resolve_overlaps(events, hook, cmap.total, cid)

    music = d.get("music")
    graph, alabel = build_graph(ivs, base, sw, sh, layout, crop_x, d.get("punch_in", 1.07),
                                music, not args.no_loudnorm)
    graph += ";\n[base][1:v]overlay=0:0:format=auto:eof_action=pass[out]"
    os.makedirs(args.out, exist_ok=True)
    gpath = os.path.join(args.out, f".graph_{cid}.txt")
    with open(gpath, "w") as f:
        f.write(graph)
    name = f"reel_{cid}_{style}" + ("_preview" if args.preview else "") + ".mp4"
    outp = os.path.join(args.out, name)
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
           "-ss", f"{base:.3f}", "-t", f"{win_end - base:.3f}", "-i", src,
           "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
           "-thread_queue_size", "512", "-i", "-"]
    if music:
        cmd += ["-stream_loop", "-1", "-i", music["file"]]
    cmd += [flag, gpath, "-map", "[out]", "-map", alabel, "-t", f"{total:.3f}",
            "-c:v", "libx264", "-preset", args.preset, "-crf", str(args.crf), "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", outp]
    log = open(os.path.join(args.out, f".ffmpeg_{cid}.log"), "w")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=log)
    nframes = int(math.ceil(total * FPS))
    print(f"[{cid}] {style:9s} theme={d.get('theme') or THEME_ORDER[idx % len(THEME_ORDER)]:8s} "
          f"{total:5.1f}s ({len(ivs)} cuts)  '{d.get('hook', '')[:50]}'")
    t_start = time.time()
    try:
        for f in range(nframes):
            t = f / FPS
            dim = max([e.dim(t) for e in events] + [0.0])
            canvas = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * dim)))
            for e in events:
                e.draw(canvas, t)
            track.draw(canvas, t)
            for e in top_events:
                e.draw(canvas, t)
            if d.get("progress_bar", True):
                gfx.draw_progress(canvas, t, cmap.total, th)
            proc.stdin.write(canvas.tobytes())
            if f % 90 == 89:
                print(f"      {f + 1}/{nframes} frames  ({(f + 1) / (time.time() - t_start):.1f} fps)", end="\r")
        proc.stdin.close()
    except BrokenPipeError:
        pass
    rc = proc.wait()
    log.close()
    if rc != 0:
        print(f"\n[{cid}] ffmpeg failed (see {args.out}/.ffmpeg_{cid}.log):")
        print(open(os.path.join(args.out, f'.ffmpeg_{cid}.log')).read()[-1500:])
        return
    print(f"[{cid}] -> {outp}  ({time.time() - t_start:.0f}s)          ")
    os.remove(gpath)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clips")
    ap.add_argument("--only", default=None, help="comma-separated clip ids")
    ap.add_argument("--preview", type=float, default=None, help="render only the first N seconds")
    ap.add_argument("--out", default=None)
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--preset", default="medium")
    ap.add_argument("--no-face", action="store_true", help="skip face detection, centre crop")
    ap.add_argument("--no-loudnorm", action="store_true")
    ap.add_argument("--jobs", type=int, default=1, help="reels rendered in parallel (try 2-4)")
    args = ap.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or not shutil.which("ffprobe"):
        sys.exit("ffmpeg/ffprobe not found on PATH. Install FFmpeg first (see README).")
    base_dir = os.path.dirname(os.path.abspath(args.clips))
    with open(args.clips, encoding="utf-8") as f:
        cfg = json.load(f)
    rel = lambda p: p if os.path.isabs(p) else os.path.join(base_dir, p)
    with open(rel(cfg.get("transcript", "transcript.json")), encoding="utf-8") as f:
        tj = json.load(f)
    cfg["_words"] = tj["words"]
    cfg["source"] = rel(os.path.expanduser(cfg.get("source") or tj.get("source", "")))
    if not os.path.exists(cfg["source"]):
        sys.exit(f"source video not found: {cfg['source']}")
    for c in cfg["clips"]:
        for k in ("music",):
            if c.get(k) and not os.path.isabs(c[k]["file"]):
                c[k]["file"] = rel(c[k]["file"])
    args.out = args.out or os.path.join(base_dir, "out")
    flag = filter_flag(ffmpeg)
    only = set(args.only.split(",")) if args.only else None
    todo = []
    for i, clip in enumerate(cfg["clips"]):
        cid = str(clip.get("id", i + 1)).zfill(2)
        if only and cid not in only and str(clip.get("id", i + 1)) not in only:
            continue
        todo.append((i, clip))
    if args.jobs > 1 and len(todo) > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=args.jobs) as ex:
            futs = [ex.submit(render_clip, cfg, c, i, args, ffmpeg, flag) for i, c in todo]
            for f in futs:
                f.result()
    else:
        for i, clip in todo:
            render_clip(cfg, clip, i, args, ffmpeg, flag)


if __name__ == "__main__":
    main()
