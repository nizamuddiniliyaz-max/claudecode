"""Shared helpers: easing, fonts, themes, supersampled drawing layers, compositing."""
import math
import os
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "fonts")
W, H = 1080, 1920
FPS = 30

# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def out_cubic(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def in_cubic(t):
    t = clamp(t)
    return t ** 3


def in_out_cubic(t):
    t = clamp(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def out_back(t, s=1.70158):
    t = clamp(t)
    return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2


def out_elastic(t):
    t = clamp(t)
    if t in (0.0, 1.0):
        return t
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1


def fade_window(t, dur, fin=0.2, fout=0.25):
    """0..1 opacity for an element alive during [0, dur]."""
    if t < 0 or t > dur:
        return 0.0
    a = clamp(t / fin) if fin > 0 else 1.0
    b = clamp((dur - t) / fout) if fout > 0 else 1.0
    return min(a, b)


# ---------------------------------------------------------------- themes
THEMES = {
    "midnight": dict(panel=(9, 13, 30), ink=(255, 255, 255), accent=(255, 196, 0),
                     accent2=(92, 124, 255), mute=(150, 160, 195)),
    "ember": dict(panel=(26, 9, 9), ink=(255, 248, 240), accent=(255, 90, 54),
                  accent2=(255, 190, 120), mute=(196, 160, 150)),
    "forest": dict(panel=(7, 24, 20), ink=(240, 255, 248), accent=(60, 226, 160),
                   accent2=(255, 214, 102), mute=(140, 184, 166)),
    "violet": dict(panel=(18, 10, 36), ink=(255, 255, 255), accent=(255, 92, 200),
                   accent2=(126, 87, 255), mute=(170, 150, 210)),
}


def theme(name):
    return THEMES.get(name or "midnight", THEMES["midnight"])


# ---------------------------------------------------------------- fonts
FONT_FILES = {
    "anton": ("Anton-Regular.ttf", None),
    "bebas": ("BebasNeue-Regular.ttf", None),
    "marker": ("PermanentMarker-Regular.ttf", None),
    "poppins": ("Poppins-Bold.ttf", None),
    "poppins-semi": ("Poppins-SemiBold.ttf", None),
    "montserrat": ("Montserrat[wght].ttf", 800),
    "montserrat-med": ("Montserrat[wght].ttf", 600),
    "playfair": ("PlayfairDisplay-Italic[wght].ttf", 700),
    "caveat": ("Caveat[wght].ttf", 700),
}


@lru_cache(maxsize=256)
def font(key, size):
    fname, weight = FONT_FILES[key]
    f = ImageFont.truetype(os.path.join(FONT_DIR, fname), int(size))
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


@lru_cache(maxsize=1)
def emoji_font():
    p = os.path.join(FONT_DIR, "NotoColorEmoji.ttf")
    return ImageFont.truetype(p, 109) if os.path.exists(p) else None


@lru_cache(maxsize=128)
def emoji_sprite(char, px):
    f = emoji_font()
    if f is None:
        return None
    im = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), char, font=f, embedded_color=True)
    box = im.getbbox()
    if not box:
        return None
    im = im.crop(box)
    scale = px / max(im.size)
    return im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)


def text_size(txt, f, stroke=0):
    l, t, r, b = f.getbbox(txt, stroke_width=stroke)
    return r - l, b - t


# ---------------------------------------------------------------- compositing
def blit(dst, src, x, y, opacity=1.0):
    """alpha-composite src onto dst at (x, y); clips to bounds; optional opacity."""
    x, y = int(round(x)), int(round(y))
    if opacity <= 0.003:
        return
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1 = min(src.width, dst.width - x)
    sy1 = min(src.height, dst.height - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    sub = src.crop((sx0, sy0, sx1, sy1))
    if opacity < 0.997:
        a = sub.getchannel("A").point(lambda v: int(v * opacity))
        sub.putalpha(a)
    dst.alpha_composite(sub, (x + sx0, y + sy0))


def tint(img, rgb):
    """return img recoloured to rgb, alpha preserved"""
    out = Image.new("RGBA", img.size, tuple(rgb) + (255,))
    out.putalpha(img.getchannel("A"))
    return out


class SS:
    """Supersampled drawing layer: draw at `k`x, downsample on finish() for smooth edges.

    Every primitive is drawn on a small temporary layer and alpha-composited, because
    ImageDraw on an RGBA image overwrites pixels (it does not blend translucent fills).
    """

    def __init__(self, w, h, k=2):
        self.w, self.h, self.k = int(w), int(h), k
        self.img = Image.new("RGBA", (self.w * k, self.h * k), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)  # only used for text measuring

    def _over(self, bbox, fn):
        x0, y0 = max(0, int(bbox[0]) - 3), max(0, int(bbox[1]) - 3)
        x1, y1 = min(self.img.width, int(bbox[2]) + 4), min(self.img.height, int(bbox[3]) + 4)
        if x1 <= x0 or y1 <= y0:
            return
        tmp = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
        fn(ImageDraw.Draw(tmp), -x0, -y0)
        self.img.alpha_composite(tmp, (x0, y0))

    def rrect(self, box, r, fill=None, outline=None, width=0):
        k = self.k
        b = [c * k for c in box]
        pad = width * k
        self._over((b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad), lambda d, ox, oy: d.rounded_rectangle(
            (b[0] + ox, b[1] + oy, b[2] + ox, b[3] + oy), r * k, fill=fill, outline=outline, width=int(width * k)))

    def poly(self, pts, fill=None, outline=None, width=0):
        k = self.k
        P = [(x * k, y * k) for x, y in pts]
        xs, ys = [p[0] for p in P], [p[1] for p in P]
        pad = width * k + 2

        def fn(d, ox, oy):
            Q = [(x + ox, y + oy) for x, y in P]
            if fill:
                d.polygon(Q, fill=fill)
            if outline:
                d.line(Q + [Q[0]], fill=outline, width=max(1, int(width * k)), joint="curve")
        self._over((min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad), fn)

    def line(self, pts, fill, width):
        k = self.k
        P = [(x * k, y * k) for x, y in pts]
        xs, ys = [p[0] for p in P], [p[1] for p in P]
        pad = width * k
        self._over((min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad),
                   lambda d, ox, oy: d.line([(x + ox, y + oy) for x, y in P], fill=fill,
                                            width=int(width * k), joint="curve"))

    def ellipse(self, box, fill=None, outline=None, width=0):
        k = self.k
        b = [c * k for c in box]
        pad = width * k
        self._over((b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad), lambda d, ox, oy: d.ellipse(
            (b[0] + ox, b[1] + oy, b[2] + ox, b[3] + oy), fill=fill, outline=outline, width=int(width * k)))

    def text(self, xy, txt, fkey, size, fill, anchor="mm", stroke=0, stroke_fill=None):
        k = self.k
        f = font(fkey, size * k)
        pos = (xy[0] * k, xy[1] * k)
        bb = self.d.textbbox(pos, txt, font=f, anchor=anchor, stroke_width=int(stroke * k))
        self._over(bb, lambda d, ox, oy: d.text((pos[0] + ox, pos[1] + oy), txt, font=f, fill=fill,
                                                anchor=anchor, stroke_width=int(stroke * k),
                                                stroke_fill=stroke_fill))

    def finish(self):
        if self.k == 1:
            return self.img
        return self.img.resize((self.w, self.h), Image.LANCZOS)


def with_alpha(rgb, a):
    return tuple(rgb) + (int(clamp(a, 0, 1) * 255),)


def mix(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))
