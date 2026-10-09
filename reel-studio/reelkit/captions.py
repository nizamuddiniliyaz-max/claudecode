"""Animated word-by-word captions drawn with Pillow. Six distinct styles to A/B test."""
import bisect
import math
import re
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter

from .util import (SS, W, blit, clamp, font, lerp, mix, out_back, out_cubic)

GOLD = (255, 206, 102)

STYLES = {
    # chunky Anton caps, white with black outline, active word turns yellow and pops
    "impact": dict(font="anton", size=118, case="upper", max_words=3, max_chars=18,
                   fill=(255, 255, 255), active_fill=(255, 214, 0), stroke=10,
                   stroke_fill=(0, 0, 0), shadow=True, pop_from=0.7, active_scale=1.1,
                   pop_dur=0.13, reveal="all", future_alpha=1.0, strip_punct=True),
    # Poppins bold, active word sits on a coloured rounded box that jumps word to word
    "boxed": dict(font="poppins", size=86, case="lower", max_words=4, max_chars=26,
                  fill=(255, 255, 255), active_fill=(255, 255, 255), stroke=0,
                  stroke_fill=None, shadow=True, box=(124, 58, 237), pop_from=0.88,
                  active_scale=1.0, pop_dur=0.12, reveal="all", future_alpha=0.9,
                  strip_punct=True),
    # Playfair italic, words fade in one by one, key words get bigger and gold with a rule
    "editorial": dict(font="playfair", size=96, case="asis", max_words=5, max_chars=30,
                      fill=(255, 255, 255), active_fill=(255, 255, 255), stroke=0,
                      stroke_fill=None, shadow=True, pop_from=0.9, active_scale=1.0,
                      pop_dur=0.2, reveal="progressive", fade_in=0.16, emphasis_fill=GOLD,
                      emphasis_scale=1.3, underline="emphasis", strip_punct=False),
    # hand-drawn marker caps, tilted words in rotating colours, scribble under the live word
    "marker": dict(font="marker", size=104, case="upper", max_words=3, max_chars=17,
                   fill=(255, 255, 255), active_fill=(255, 255, 255), stroke=8,
                   stroke_fill=(0, 0, 0), shadow=True, pop_from=0.6, active_scale=1.0,
                   pop_dur=0.16, reveal="progressive", fade_in=0.05,
                   cycle=[(255, 255, 255), (255, 230, 0), (255, 120, 205)],
                   wobble=[-3.0, 2.0, -1.5, 3.0], underline="scribble", strip_punct=True),
    # tall Bebas, two lines staggered left/right with different sizes and colours
    "stack": dict(font="bebas", size=215, case="upper", max_words=2, max_chars=20,
                  fill=(255, 255, 255), active_fill=(255, 255, 255), stroke=0,
                  stroke_fill=None, shadow=True, pop_from=0.7, active_scale=1.0,
                  pop_dur=0.16, reveal="progressive", fade_in=0.05, layout="stack",
                  line_scale=[1.0, 0.68], line_fill=[(255, 255, 255), (255, 84, 84)],
                  line_dx=[-70, 90], strip_punct=True),
    # minimal Montserrat, whole phrase visible but dim, live word lights up with a soft glow
    "glow": dict(font="montserrat-med", size=80, case="lower", max_words=4, max_chars=28,
                 fill=(255, 255, 255), active_fill=(255, 255, 255), stroke=0,
                 stroke_fill=None, shadow=False, glow=(120, 170, 255), pop_from=0.94,
                 active_scale=1.04, pop_dur=0.14, reveal="all", future_alpha=0.32,
                 past_alpha=0.92, strip_punct=True),
}

_PUNCT = re.compile(r"[^\w'’%$&@#+-]+", re.UNICODE)


def norm(w):
    return _PUNCT.sub("", w.lower())


def make_chunks(words, style):
    mw, mc = style["max_words"], style["max_chars"]
    chunks, cur = [], []
    for w in words:
        if cur:
            chars = sum(len(x["text"]) + 1 for x in cur) + len(w["text"])
            gap = w["start"] - cur[-1]["end"]
            ends = cur[-1]["raw"].rstrip().endswith((".", "?", "!"))
            if len(cur) >= mw or chars > mc or gap > 0.45 or ends:
                chunks.append(cur)
                cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    return chunks


def prep_words(words, style):
    """words: [{'w','start','end'}] in OUTPUT time. returns display words."""
    out = []
    for i, w in enumerate(words):
        raw = w["w"].strip()
        t = raw
        if style.get("strip_punct"):
            t = _PUNCT.sub("", raw) or raw
        if style["case"] == "upper":
            t = t.upper()
        elif style["case"] == "lower":
            t = t.lower()
        out.append(dict(text=t, raw=raw, start=w["start"], end=w["end"], norm=norm(raw), idx=i))
    return out


# ---------------------------------------------------------------- sprites
@lru_cache(maxsize=4096)
def word_sprite(text, fkey, size, fill, stroke, stroke_fill, shadow, glow):
    f = font(fkey, size)
    asc, desc = f.getmetrics()
    adv = int(math.ceil(f.getlength(text)))
    pad = stroke + 14 + (26 if glow else 0)
    w, h = adv + 2 * pad, asc + desc + 2 * pad
    base = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    xy = (pad, pad + asc)
    if shadow:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((xy[0], xy[1] + 7), text, font=f, fill=(0, 0, 0, 170), anchor="ls",
                                stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
        base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)))
    if glow:
        gl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(gl).text(xy, text, font=f, fill=tuple(glow) + (255,), anchor="ls")
        gl = gl.filter(ImageFilter.GaussianBlur(14))
        base.alpha_composite(gl)
        base.alpha_composite(gl)
    d.text(xy, text, font=f, fill=tuple(fill) + (255,), anchor="ls", stroke_width=stroke,
           stroke_fill=(tuple(stroke_fill) + (255,)) if stroke_fill else None)
    return base, adv, pad, asc, desc


@lru_cache(maxsize=2048)
def rotated(sprite_key, angle):
    spr = word_sprite(*sprite_key)[0]
    return spr.rotate(angle, resample=Image.BICUBIC, expand=True)


@lru_cache(maxsize=512)
def box_sprite(w, h, r, color):
    ss = SS(w, h, 2)
    ss.rrect((0, 0, w, h), r, fill=tuple(color) + (255,))
    return ss.finish()


@lru_cache(maxsize=256)
def scribble_sprite(w, color):
    h = 34
    ss = SS(w, h, 2)
    pts, x, up = [], 4, True
    while x < w - 4:
        pts.append((x, 8 if up else 26))
        x += 22
        up = not up
    pts.append((w - 4, 17))
    if len(pts) > 1:
        ss.line(pts, tuple(color) + (255,), 7)
    return ss.finish()


def _scaled(img, s):
    if abs(s - 1.0) < 0.004:
        return img
    return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BICUBIC)


# ---------------------------------------------------------------- layout + draw
class CaptionTrack:
    def __init__(self, words, style_name, emphasis=None, cy=1170):
        self.style = STYLES[style_name]
        self.name = style_name
        self.cy = cy
        self.emphasis = {norm(e) for e in (emphasis or [])}
        self.words = prep_words(words, self.style)
        self.chunks = make_chunks(self.words, self.style)
        self.starts = [c[0]["start"] - 0.02 for c in self.chunks]
        self.ends = []
        for i, c in enumerate(self.chunks):
            last = c[-1]["end"] + 0.4
            nxt = self.starts[i + 1] if i + 1 < len(self.chunks) else last
            self.ends.append(min(last, nxt))
        if self.style.get("emphasis_fill") and not self.emphasis:
            self.auto_emph = True
        else:
            self.auto_emph = False

    def _active_chunk(self, t):
        i = bisect.bisect_right(self.starts, t) - 1
        if i < 0 or t >= self.ends[i]:
            return None, -1
        return self.chunks[i], i

    def _is_emph(self, w, chunk):
        if not self.style.get("emphasis_fill"):
            return False
        if self.emphasis:
            return w["norm"] in self.emphasis
        longest = max(chunk, key=lambda x: len(x["norm"]))
        return w is longest and len(w["norm"]) >= 6

    def draw(self, canvas, t):
        chunk, ci = self._active_chunk(t)
        if chunk is None:
            return
        st = self.style
        if st.get("layout") == "stack":
            self._draw_stack(canvas, chunk, ci, t)
        else:
            self._draw_flow(canvas, chunk, ci, t)

    # per-word timing/state
    def _state(self, w, chunk, t):
        st = self.style
        age = t - w["start"]
        i = chunk.index(w)
        end_eff = chunk[i + 1]["start"] if i + 1 < len(chunk) else self.ends[self.chunks.index(chunk)]
        active = age >= 0 and t < end_eff
        past = t >= end_eff
        pd = st["pop_dur"]
        if age < 0:
            scale = 1.0
        elif age < pd:
            scale = lerp(st["pop_from"], st["active_scale"], out_back(age / pd))
        elif active:
            scale = st["active_scale"]
        else:
            k = out_cubic((t - end_eff) / 0.08)
            scale = lerp(st["active_scale"], 1.0, k)
        if st["reveal"] == "progressive":
            if age < 0:
                alpha = 0.0
            else:
                alpha = clamp(age / st.get("fade_in", 0.1))
        else:
            if age < 0:
                alpha = st.get("future_alpha", 1.0)
            elif active:
                alpha = 1.0
            else:
                alpha = st.get("past_alpha", 1.0)
        return age, active, scale, alpha

    def _fill(self, w, active, idx_in_chunk, chunk, ci):
        st = self.style
        if self._is_emph(w, chunk):
            return st["emphasis_fill"]
        if st.get("cycle"):
            return st["cycle"][(ci + idx_in_chunk) % len(st["cycle"])]
        return st["active_fill"] if active else st["fill"]

    def _spr_key(self, text, size, fill):
        st = self.style
        return (text, st["font"], int(size), tuple(fill), st["stroke"],
                tuple(st["stroke_fill"]) if st["stroke_fill"] else None,
                bool(st.get("shadow")), tuple(st["glow"]) if st.get("glow") else None)

    def _draw_flow(self, canvas, chunk, ci, t):
        st = self.style
        max_w = 920
        space = st["size"] * 0.24 + 1.6 * st["stroke"] + (36 if st.get("box") else 0)
        items = []
        for i, w in enumerate(chunk):
            age, active, scale, alpha = self._state(w, chunk, t)
            emph = self._is_emph(w, chunk)
            size = st["size"] * (st.get("emphasis_scale", 1.0) if emph else 1.0)
            fill = self._fill(w, active, i, chunk, ci)
            key = self._spr_key(w["text"], size, fill)
            spr, adv, pad, asc, desc = word_sprite(*key)
            items.append(dict(w=w, key=key, adv=adv, pad=pad, asc=asc, desc=desc, active=active,
                              scale=scale, alpha=alpha, age=age, emph=emph, i=i, fill=fill))
        # wrap into lines
        lines, cur, cw = [], [], 0
        for it in items:
            add = it["adv"] + (space if cur else 0)
            if cur and cw + add > max_w:
                lines.append(cur)
                cur, cw = [], 0
                add = it["adv"]
            cur.append(it)
            cw += add
        if cur:
            lines.append(cur)
        line_h = [max(it["asc"] + it["desc"] for it in ln) for ln in lines]
        gap = 14
        total = sum(line_h) + gap * (len(lines) - 1)
        y = self.cy - total / 2
        for ln, lh in zip(lines, line_h):
            lw = sum(it["adv"] for it in ln) + space * (len(ln) - 1)
            x = W / 2 - lw / 2
            base_asc = max(it["asc"] for it in ln)
            for it in ln:
                self._blit_word(canvas, it, x, y + base_asc, chunk, ci)
                x += it["adv"] + space
            y += lh + gap

    def _blit_word(self, canvas, it, x, baseline, chunk, ci):
        st = self.style
        spr, adv, pad, asc, desc = word_sprite(*it["key"])
        alpha = it["alpha"]
        if alpha <= 0.01:
            return
        cx = x + adv / 2
        top = baseline - asc - pad
        cy_w = top + spr.height / 2
        # active box
        if st.get("box") and it["active"]:
            bw, bh = adv + 44, asc * 1.0
            bs = box_sprite(int(bw), int(bh), 22, tuple(st["box"]))
            bs = _scaled(bs, it["scale"])
            box_cy = baseline - asc * 0.34
            blit(canvas, bs, cx - bs.width / 2, box_cy - bs.height / 2, alpha)
        img = spr
        if st.get("wobble"):
            ang = st["wobble"][(it["w"]["idx"]) % len(st["wobble"])]
            img = rotated(it["key"], ang)
        img = _scaled(img, it["scale"])
        # slight rise on appearance for progressive styles
        rise = 0.0
        if st["reveal"] == "progressive" and it["age"] < 0.2 and it["age"] >= 0:
            rise = (1 - out_cubic(it["age"] / 0.2)) * 22
        blit(canvas, img, cx - img.width / 2, cy_w - img.height / 2 + rise, alpha)
        # underline decorations
        ul = st.get("underline")
        if ul == "scribble" and it["active"]:
            k = out_cubic(it["age"] / 0.18)
            sw = int(adv * max(0.15, k))
            if sw > 20:
                blit(canvas, scribble_sprite(sw, (255, 214, 0)), cx - sw / 2, baseline + 2)
        elif ul == "emphasis" and it["emph"] and it["age"] >= 0:
            k = out_cubic(it["age"] / 0.35)
            sw = int(adv * k)
            if sw > 4:
                bar = Image.new("RGBA", (sw, 5), tuple(st["emphasis_fill"]) + (255,))
                blit(canvas, bar, cx - adv / 2, baseline + desc * 0.55, alpha)

    def _draw_stack(self, canvas, chunk, ci, t):
        st = self.style
        items = []
        for i, w in enumerate(chunk):
            age, active, scale, alpha = self._state(w, chunk, t)
            ls = st["line_scale"][i % len(st["line_scale"])]
            fill = st["line_fill"][i % len(st["line_fill"])]
            key = self._spr_key(w["text"], st["size"] * ls, fill)
            spr, adv, pad, asc, desc = word_sprite(*key)
            items.append((w, key, adv, pad, asc, desc, scale, alpha, i, age))
        heights = [it[4] + it[5] - 30 for it in items]
        total = sum(heights)
        y = self.cy - total / 2
        for (w, key, adv, pad, asc, desc, scale, alpha, i, age), hh in zip(items, heights):
            if alpha > 0.01:
                spr = word_sprite(*key)[0]
                img = _scaled(spr, scale)
                dx = st["line_dx"][i % len(st["line_dx"])]
                slide = (1 - out_cubic(age / 0.18)) * (-120 if i % 2 == 0 else 120) if age < 0.18 else 0
                cx = W / 2 + dx + slide
                cyw = y + hh / 2 + 6
                blit(canvas, img, cx - img.width / 2, cyw - img.height / 2, alpha)
            y += hh
