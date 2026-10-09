"""Silence/pacing trim (driven by word timestamps) and the FFmpeg filter graph."""
import bisect
import json
import os
import subprocess
import tempfile

from .util import FPS, H, W


def probe(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "json", path])
    s = json.loads(out)["streams"][0]
    return int(s["width"]), int(s["height"])


def keep_intervals(words, start, end, max_gap=0.35, pre=0.06, post=0.12):
    """Source-time intervals to keep. Pauses longer than max_gap are cut down to pre+post."""
    ivs = []
    for w in words:
        if w["end"] <= start or w["start"] >= end:
            continue
        a = max(start, w["start"] - pre)
        b = min(end, w["end"] + post)
        if ivs and a - ivs[-1][1] <= max_gap:
            ivs[-1][1] = max(ivs[-1][1], b)
        else:
            ivs.append([a, b])
    return ivs


class CutMap:
    def __init__(self, ivs):
        self.ivs = ivs
        self.out_starts, acc = [], 0.0
        for a, b in ivs:
            self.out_starts.append(acc)
            acc += b - a
        self.total = acc
        self.src_starts = [a for a, _ in ivs]

    def __call__(self, t):
        if not self.ivs:
            return 0.0
        i = bisect.bisect_right(self.src_starts, t) - 1
        if i < 0:
            return 0.0
        a, b = self.ivs[i]
        if t <= b:
            return self.out_starts[i] + (t - a)
        # t falls in a removed gap -> snap to the start of the next kept interval
        return self.out_starts[i] + (b - a)


def remap_words(words, cmap, start, end):
    out = []
    for w in words:
        if w["end"] <= start or w["start"] >= end:
            continue
        s, e = cmap(w["start"]), cmap(w["end"])
        if e <= s:
            e = s + 0.12
        out.append(dict(w=w["w"], start=s, end=e))
    return out


def _even(v):
    return int(v) // 2 * 2


def build_graph(ivs, base, src_w, src_h, layout, crop_x, punch, music, loudnorm):
    """returns (filter_complex text, video label, audio label)"""
    parts, vlabels = [], []
    cw = _even(src_h * 9 / 16)
    cw = min(cw, _even(src_w))
    x = max(0, min(src_w - cw, _even(crop_x * src_w - cw / 2))) if crop_x is not None else _even((src_w - cw) / 2)
    fade = 0.012
    for i, (a, b) in enumerate(ivs):
        a0, b0 = a - base, b - base
        d = b0 - a0
        vf = f"[0:v]trim=start={a0:.4f}:end={b0:.4f},setpts=PTS-STARTPTS"
        if layout == "crop":
            if punch and punch > 1.0 and i % 2 == 1:
                z = punch
                zw, zh = _even(cw / z), _even(src_h / z)
                zx = x + (cw - zw) / 2
                zy = (src_h - zh) / 2
                vf += f",crop={zw}:{zh}:{int(zx)}:{int(zy)}"
            else:
                vf += f",crop={cw}:{src_h}:{x}:0"
            vf += f",scale={W}:{H}:flags=lanczos,setsar=1"
        vf += f"[v{i}]"
        parts.append(vf)
        af = (f"[0:a]atrim=start={a0:.4f}:end={b0:.4f},asetpts=PTS-STARTPTS,"
              f"afade=t=in:st=0:d={fade},afade=t=out:st={max(0, d - fade):.4f}:d={fade}[a{i}]")
        parts.append(af)
        vlabels.append(f"[v{i}][a{i}]")
    n = len(ivs)
    parts.append("".join(vlabels) + f"concat=n={n}:v=1:a=1[cv][ca0]")
    if layout == "crop":
        parts.append(f"[cv]fps={FPS},format=yuv420p[base]")
    else:  # "fit": whole 16:9 frame centred over a blurred, darkened copy of itself
        parts.append(
            f"[cv]split[fa][fb];"
            f"[fa]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"scale=216:384,boxblur=8:2,scale={W}:{H},eq=brightness=-0.18[bg];"
            f"[fb]scale={W}:-2:flags=lanczos[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,fps={FPS},format=yuv420p[base]")
    achain = "[ca0]"
    if loudnorm:
        parts.append(f"{achain}loudnorm=I=-16:TP=-1.5:LRA=11[ca1]")
        achain = "[ca1]"
    if music:
        gain = music.get("gain_db", -20)
        parts.append(f"{achain}asplit=2[sc][mixv]")
        parts.append(f"[2:a]volume={gain}dB,aformat=channel_layouts=stereo[m0]")
        parts.append("[m0][sc]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=450[md]")
        parts.append("[mixv][md]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[aout]")
        alabel = "[aout]"
    else:
        alabel = achain
    return ";\n".join(parts), alabel


def filter_flag(ffmpeg):
    """ffmpeg >= 7 deprecates -filter_complex_script in favour of -/filter_complex."""
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "g.txt")
        with open(p, "w") as f:
            f.write("[0:v]null[o]")
        for flag in (["-filter_complex_script", p], ["-/filter_complex", p]):
            r = subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                                "nullsrc=s=16x16:d=0.1", *flag, "-map", "[o]", "-f", "null", "-"],
                               capture_output=True)
            if r.returncode == 0:
                return flag[0]
    return "-filter_complex_script"
