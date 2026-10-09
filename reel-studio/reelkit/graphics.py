"""Code-drawn motion graphics (no stock images, no web cutouts).

Every graphic is an Event: starts at t0 (output time), lives for dur seconds, and draws itself
onto the RGBA frame canvas each frame. Diagram events can take over the screen (dim the video).
"""
import math

from PIL import Image, ImageFilter

from .captions import word_sprite
from .util import (H, SS, W, blit, clamp, emoji_sprite, fade_window, font, lerp, mix,
                   out_back, out_cubic, out_elastic, in_cubic, theme, text_size)

WHITE = (255, 255, 255)


def fit_size(txt, fkey, size, max_w, min_size=18):
    while size > min_size and text_size(txt, font(fkey, size))[0] > max_w:
        size -= 2
    return size


def partial(pts, k):
    """polyline covering fraction k of its length"""
    if k >= 1:
        return pts
    lens = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    target, acc, out = sum(lens) * max(k, 0), 0.0, [pts[0]]
    for i, l in enumerate(lens):
        if acc + l <= target:
            out.append(pts[i + 1])
            acc += l
        else:
            r = (target - acc) / l if l else 0
            a, b = pts[i], pts[i + 1]
            out.append((a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r))
            break
    return out


def spr_text(txt, fkey, size, fill, stroke=0, stroke_fill=None, shadow=True, glow=None):
    return word_sprite(txt, fkey, int(size), tuple(fill), stroke,
                       tuple(stroke_fill) if stroke_fill else None, shadow,
                       tuple(glow) if glow else None)[0]


def scaled(img, s):
    if abs(s - 1) < 0.004:
        return img
    return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BICUBIC)


class Event:
    takeover = False
    top = False  # draw above captions

    def __init__(self, t0, dur, th):
        self.t0, self.dur, self.th = t0, dur, th

    def active(self, t):
        return self.t0 <= t <= self.t0 + self.dur

    def dim(self, t):
        if not self.takeover or not self.active(t):
            return 0.0
        return 0.80 * fade_window(t - self.t0, self.dur, 0.3, 0.3)

    def draw(self, canvas, t):
        if self.active(t):
            self.render(canvas, t - self.t0)

    def render(self, canvas, lt):
        raise NotImplementedError


# ------------------------------------------------------------------ hook card
class HookCard(Event):
    top = True

    def __init__(self, text, th, tag="", dur=2.9, t0=0.0, y=470):
        super().__init__(t0, dur, th)
        self.text, self.tag, self.y = text.upper(), tag.upper(), y
        words, lines, cur = self.text.split(), [], ""
        for w in words:
            if cur and len(cur) + 1 + len(w) > 15:
                lines.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        if cur:
            lines.append(cur)
        self.lines = lines[:4]

    def render(self, canvas, lt):
        th = self.th
        op = fade_window(lt, self.dur, 0.01, 0.35)
        n = len(self.lines)
        size = 132 if n <= 2 else 118
        lh = size * 0.98
        y0 = self.y - (n * lh) / 2
        # soft dark band for legibility
        band_h = int(n * lh + 190)
        band = Image.new("RGBA", (W, band_h), (0, 0, 0, 0))
        grad = Image.linear_gradient("L").resize((1, band_h))
        a = grad.point(lambda v: int(150 * (1 - abs(v - 128) / 128) ** 0.7))
        band.putalpha(a.resize((W, band_h)))
        blit(canvas, band, 0, y0 - 95, op)
        if self.tag:
            tk = out_back(lt / 0.35)
            chip = spr_text(self.tag, "poppins", 34, th["panel"], shadow=False)
            cw, ch = chip.width + 36, chip.height + 6
            ss = SS(cw, ch, 2)
            ss.rrect((0, 0, cw, ch), ch / 2, fill=th["accent"] + (255,))
            cimg = ss.finish()
            cimg.alpha_composite(chip, (18, 3))
            cimg = scaled(cimg, max(0.01, tk))
            blit(canvas, cimg, W / 2 - cimg.width / 2, y0 - 70 - cimg.height / 2, op)
        for i, line in enumerate(self.lines):
            k = out_back((lt - 0.12 * i) / 0.38)
            if k <= 0:
                continue
            last = i == n - 1 and n > 1
            fill = th["accent"] if last else WHITE
            spr = spr_text(line, "anton", size, fill, stroke=0, shadow=True)
            rise = (1 - clamp(k)) * 60
            blit(canvas, scaled(spr, 0.9 + 0.1 * clamp(k)), W / 2 - spr.width * (0.9 + 0.1 * clamp(k)) / 2,
                 y0 + i * lh - rise, op * clamp((lt - 0.12 * i) / 0.18))
        # accent rule
        k = out_cubic((lt - 0.2 * n) / 0.45)
        bw = int(300 * k)
        if bw > 2:
            ss = SS(bw, 10, 2)
            ss.rrect((0, 0, bw, 10), 5, fill=th["accent"] + (255,))
            blit(canvas, ss.finish(), W / 2 - bw / 2, y0 + n * lh + 28, op)


# ------------------------------------------------------------------ pyramid
class Pyramid(Event):
    takeover = True

    def __init__(self, t0, dur, th, labels, highlight=None, title=""):
        super().__init__(t0, dur, th)
        self.labels, self.highlight, self.title = labels, highlight, title

    def render(self, canvas, lt):
        th, labels = self.th, self.labels
        n = len(labels)
        op = fade_window(lt, self.dur, 0.2, 0.3)
        ox, oy = 0, 200
        ss = SS(W, 900, 2)
        top_y, ph = 215, 560
        top_w, base_w = 190, 880
        gap = 10
        bh = (ph - gap * (n - 1)) / n

        def hw(y):
            return top_w / 2 + (y - top_y) / ph * (base_w / 2 - top_w / 2)

        build_end = 0.3 + (n - 1) * 0.3 + 0.5
        glows = []
        pulse = 0.5 + 0.5 * math.sin(max(0.0, lt - build_end) * 5)
        for i, lab in enumerate(labels):
            ta = 0.3 + (n - 1 - i) * 0.3
            prog = out_back((lt - ta) / 0.5)
            if prog <= 0:
                continue
            y0 = top_y + i * (bh + gap)
            y1 = y0 + bh
            slide = (1 - clamp(prog)) * 80
            col = mix(th["accent"], th["accent2"], i / max(1, n - 1))
            is_hi = self.highlight is not None and i == self.highlight
            if is_hi and lt > build_end:
                col = mix(col, WHITE, 0.10 + 0.16 * pulse)
            a = int(255 * clamp(prog))
            pts = [(W / 2 - hw(y0), y0 + slide), (W / 2 + hw(y0), y0 + slide),
                   (W / 2 + hw(y1), y1 + slide), (W / 2 - hw(y1), y1 + slide)]
            if is_hi and lt > build_end:
                glow = Image.new("RGBA", (W, 900), (0, 0, 0, 0))
                gs = SS(W, 900, 1)
                gs.poly([(x, y) for x, y in pts], fill=th["accent"] + (int(200 * (0.35 + 0.65 * pulse)),))
                glow = gs.finish().filter(ImageFilter.GaussianBlur(26))
                glows.append(glow)
            # soft contact shadow, body, top shine, bottom edge
            ss.poly([(x, y + 9) for x, y in pts], fill=(0, 0, 0, int(90 * clamp(prog))))
            ss.poly(pts, fill=col + (a,))
            shine = [pts[0], pts[1], (pts[1][0] + (pts[2][0] - pts[1][0]) * 0.42, pts[1][1] + (pts[2][1] - pts[1][1]) * 0.42),
                     (pts[0][0] + (pts[3][0] - pts[0][0]) * 0.42, pts[0][1] + (pts[3][1] - pts[0][1]) * 0.42)]
            ss.poly(shine, fill=WHITE + (int(46 * clamp(prog)),))
            ss.line([pts[3], pts[2]], (0, 0, 0, int(70 * clamp(prog))), 5)
            if is_hi and lt > build_end:
                ss.poly(pts, outline=WHITE + (int(210 * pulse),), width=5)
            inner = 2 * hw(y0) - 30
            fs = fit_size(lab.upper(), "poppins", min(46, int(bh * 0.5)), max(100, inner))
            tcol = th["panel"] if sum(col) > 380 else WHITE
            ss.text((W / 2, (y0 + y1) / 2 + slide), lab.upper(), "poppins", fs, tcol + (a,))
        for g in glows:
            blit(canvas, g, ox, oy, op)
        layer = ss.finish()
        blit(canvas, layer, ox, oy, op)
        if self.title:
            k = out_cubic(lt / 0.4)
            spr = spr_text(self.title.upper(), "anton", 92, th["accent"], shadow=True)
            blit(canvas, spr, W / 2 - spr.width / 2, 205 - 30 * (1 - k), op * k)


# ------------------------------------------------------------------ org tree
def _parse(spec, depth=0):
    if isinstance(spec, str):
        spec = {"label": spec}
    return {"label": spec["label"], "depth": depth,
            "children": [_parse(c, depth + 1) for c in spec.get("children", [])]}


def _layout(node, counter):
    if not node["children"]:
        node["xs"] = counter[0]
        counter[0] += 1
    else:
        for c in node["children"]:
            _layout(c, counter)
        node["xs"] = (node["children"][0]["xs"] + node["children"][-1]["xs"]) / 2


def _flat(node, out=None):
    out = [] if out is None else out
    out.append(node)
    for c in node["children"]:
        _flat(c, out)
    return out


class OrgTree(Event):
    takeover = True

    def __init__(self, t0, dur, th, tree, highlight=None, title=""):
        super().__init__(t0, dur, th)
        self.root = _parse(tree)
        cnt = [0]
        _layout(self.root, cnt)
        self.leaves = cnt[0]
        self.nodes = _flat(self.root)
        self.levels = max(n["depth"] for n in self.nodes) + 1
        self.highlight = {h.lower() for h in (highlight or [])}
        self.title = title

    def render(self, canvas, lt):
        th = self.th
        op = fade_window(lt, self.dur, 0.2, 0.3)
        oy = 200
        ss = SS(W, 900, 2)
        left, avail = 60, W - 120
        slot = avail / self.leaves
        nw = min(300, slot - 16)
        nh = 96
        top_y = 190
        gapy = min(260, (600) / max(1, self.levels - 1)) if self.levels > 1 else 0
        fs0 = 40
        pos = {}
        for nd in self.nodes:
            pos[id(nd)] = (left + (nd["xs"] + 0.5) * slot, top_y + nd["depth"] * gapy)

        def ta(nd):
            return 0.25 + nd["depth"] * 0.5

        # edges first
        for nd in self.nodes:
            px, py = pos[id(nd)]
            for c in nd["children"]:
                cx, cy = pos[id(c)]
                k = out_cubic((lt - ta(c) + 0.25) / 0.5)
                if k <= 0:
                    continue
                my = (py + cy) / 2
                pts = [(px, py + nh / 2), (px, my), (cx, my), (cx, cy - nh / 2)]
                hi = nd["label"].lower() in self.highlight and c["label"].lower() in self.highlight
                col = th["accent"] if hi else mix(th["mute"], WHITE, 0.2)
                ss.line(partial(pts, k), col + (230,), 5 if hi else 4)
        for nd in self.nodes:
            x, y = pos[id(nd)]
            k = out_back((lt - ta(nd)) / 0.45)
            if k <= 0:
                continue
            s = max(0.01, k)
            hi = nd["label"].lower() in self.highlight
            w2, h2 = nw * s / 2, nh * s / 2
            fill = th["accent"] if hi else mix(th["panel"], WHITE, 0.14)
            if hi and lt > ta(nd) + 0.5:
                pulse = 0.5 + 0.5 * math.sin((lt - ta(nd)) * 5)
                ss.rrect((x - w2 - 6, y - h2 - 6, x + w2 + 6, y + h2 + 6), 22, outline=th["accent"] + (int(120 + 120 * pulse),), width=4)
            ss.rrect((x - w2, y - h2, x + w2, y + h2), 18, fill=fill + (int(255 * clamp(k)),),
                     outline=(WHITE + (140,)) if not hi else None, width=2)
            fs = fit_size(nd["label"], "poppins", fs0, nw - 22)
            tcol = th["panel"] if hi else WHITE
            ss.text((x, y), nd["label"], "poppins", max(12, int(fs * s)), tcol + (int(255 * clamp(k)),))
        blit(canvas, ss.finish(), 0, oy, op)
        if self.title:
            k = out_cubic(lt / 0.4)
            spr = spr_text(self.title.upper(), "anton", 92, th["accent"], shadow=True)
            blit(canvas, spr, W / 2 - spr.width / 2, 205 - 30 * (1 - k), op * k)


# ------------------------------------------------------------------ steps / ladder
class Steps(Event):
    takeover = True

    def __init__(self, t0, dur, th, labels, title=""):
        super().__init__(t0, dur, th)
        self.labels, self.title = labels, title

    def render(self, canvas, lt):
        th, labels = self.th, self.labels
        n = len(labels)
        op = fade_window(lt, self.dur, 0.2, 0.3)
        ss = SS(W, 900, 2)
        left, avail, base_y = 70, W - 140, 760
        gap = 14
        bw = (avail - gap * (n - 1)) / n
        unit = 470 / n
        tops = []
        for i, lab in enumerate(labels):
            ta = 0.25 + i * 0.28
            k = out_cubic((lt - ta) / 0.5)
            hgt = unit * (i + 1) * k
            x0 = left + i * (bw + gap)
            col = mix(th["accent2"], th["accent"], i / max(1, n - 1))
            if hgt > 1:
                ss.rrect((x0, base_y - hgt + 8, x0 + bw, base_y + 8), 16, fill=(0, 0, 0, 90))
                ss.rrect((x0, base_y - hgt, x0 + bw, base_y), 16, fill=col + (255,))
                ss.rrect((x0, base_y - hgt, x0 + bw * 0.45, base_y), 16, fill=WHITE + (34,))
                ss.rrect((x0, base_y - hgt, x0 + bw, base_y - hgt + 10), 5, fill=WHITE + (110,))
            tops.append((x0 + bw / 2, base_y - unit * (i + 1)))
            if k > 0.6:
                a = int(255 * clamp((k - 0.6) / 0.4))
                fs = fit_size(lab.upper(), "poppins", 42, bw - 8)
                ss.text((x0 + bw / 2, base_y - unit * (i + 1) * k - 34), lab.upper(), "poppins", fs, WHITE + (a,))
        # climbing dot
        t_dot = lt - (0.25 + n * 0.28 + 0.2)
        if t_dot > 0 and n > 1:
            pos = clamp(t_dot / (0.5 * (n - 1)), 0, 1) * (n - 1)
            i = min(int(pos), n - 2)
            f = pos - i
            x = lerp(tops[i][0], tops[i + 1][0], f)
            y = lerp(tops[i][1], tops[i + 1][1], f) - 100 - 50 * math.sin(math.pi * f)
            ss.ellipse((x - 20, y - 20, x + 20, y + 20), fill=WHITE + (255,))
            ss.ellipse((x - 34, y - 34, x + 34, y + 34), outline=th["accent"] + (160,), width=4)
        blit(canvas, ss.finish(), 0, 200, op)
        if self.title:
            k = out_cubic(lt / 0.4)
            spr = spr_text(self.title.upper(), "anton", 92, th["accent"], shadow=True)
            blit(canvas, spr, W / 2 - spr.width / 2, 205 - 30 * (1 - k), op * k)


# ------------------------------------------------------------------ keyword pop
class Keyword(Event):
    def __init__(self, t0, dur, th, text, sub="", y=430, size=150):
        super().__init__(t0, dur, th)
        self.text, self.sub, self.y, self.size = text.upper(), sub, y, size

    def render(self, canvas, lt):
        th = self.th
        op = fade_window(lt, self.dur, 0.05, 0.25)
        k = out_back(lt / 0.32)
        size = fit_size(self.text, "anton", self.size, 940)
        spr = spr_text(self.text, "anton", size, WHITE, shadow=True, glow=th["accent2"])
        s = max(0.01, lerp(0.55, 1.0, clamp(k)) if lt < 0.32 else 1.0 + 0.012 * math.sin(lt * 4))
        img = scaled(spr, s)
        cx, cy = W / 2, self.y
        # ring burst
        rk = clamp(lt / 0.55)
        if 0 < rk < 1:
            r = lerp(60, 330, out_cubic(rk))
            ss = SS(700, 700, 2)
            ss.ellipse((350 - r, 350 - r, 350 + r, 350 + r), outline=th["accent"] + (int(220 * (1 - rk)),),
                       width=int(lerp(10, 2, rk)))
            blit(canvas, ss.finish(), cx - 350, cy - 350, op)
        blit(canvas, img, cx - img.width / 2, cy - img.height / 2, op)
        # underline sweep
        uk = out_cubic((lt - 0.12) / 0.45)
        uw = int((spr.width - 60) * uk)
        if uw > 4:
            ss = SS(uw, 12, 2)
            ss.rrect((0, 0, uw, 12), 6, fill=th["accent"] + (255,))
            blit(canvas, ss.finish(), cx - (spr.width - 60) / 2, cy + size * 0.55 + 6, op)
        if self.sub:
            sk = out_cubic((lt - 0.3) / 0.35)
            sp = spr_text(self.sub, "poppins-semi", 44, th["ink"], shadow=True)
            blit(canvas, sp, cx - sp.width / 2, cy + size * 0.55 + 34 + (1 - sk) * 20, op * sk)


# ------------------------------------------------------------------ stat counter
class Stat(Event):
    def __init__(self, t0, dur, th, value, suffix="", label="", prefix="", y=560):
        super().__init__(t0, dur, th)
        self.value, self.suffix, self.label, self.prefix, self.y = float(value), suffix, label, prefix, y

    def render(self, canvas, lt):
        th = self.th
        op = fade_window(lt, self.dur, 0.2, 0.3)
        k = out_back(lt / 0.4)
        cw, ch = 800, 450
        ss = SS(cw, ch, 2)
        ss.rrect((0, 0, cw, ch), 40, fill=th["panel"] + (225,), outline=th["accent"] + (255,), width=4)
        card = ss.finish()
        v = self.value * out_cubic((lt - 0.15) / 1.0)
        num = f"{self.prefix}{int(round(v)) if self.value == int(self.value) else round(v, 1)}{self.suffix}"
        nsize = fit_size(num, "anton", 230, cw - 80)
        ns = spr_text(num, "anton", nsize, th["accent"], shadow=True)
        card.alpha_composite(ns, (cw // 2 - ns.width // 2, 20))
        if self.label:
            ls = fit_size(self.label, "poppins-semi", 40, cw - 70)
            lb = spr_text(self.label, "poppins-semi", ls, th["ink"], shadow=False)
            card.alpha_composite(lb, (cw // 2 - lb.width // 2, ch - lb.height - 36))
        img = scaled(card, max(0.01, lerp(0.8, 1.0, clamp(k))))
        blit(canvas, img, W / 2 - img.width / 2, self.y - img.height / 2, op)


# ------------------------------------------------------------------ emoji pop
class EmojiPop(Event):
    def __init__(self, t0, dur, th, char, x=0.5, y=0.3, size=240):
        super().__init__(t0, dur, th)
        self.char, self.fx, self.fy, self.size = char, x, y, size
        self.ok = emoji_sprite(char, size) is not None

    def render(self, canvas, lt):
        if not self.ok:
            return
        op = fade_window(lt, self.dur, 0.05, 0.25)
        k = out_elastic(lt / 0.7)
        spr = emoji_sprite(self.char, self.size)
        s = max(0.01, k)
        img = scaled(spr, s)
        bob = math.sin(lt * 3.2) * 10
        tilt = math.sin(lt * 2.4) * 6
        img = img.rotate(tilt, resample=Image.BICUBIC, expand=True)
        # soft shadow
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sh.putalpha(img.getchannel("A").point(lambda v: int(v * 0.35)))
        x, y = self.fx * W, self.fy * H + bob
        blit(canvas, sh, x - img.width / 2 + 6, y - img.height / 2 + 12, op)
        blit(canvas, img, x - img.width / 2, y - img.height / 2, op)


# ------------------------------------------------------------------ progress bar
def draw_progress(canvas, t, total, th):
    k = clamp(t / max(total, 0.01))
    x0, x1, y, h = 70, W - 70, 118, 8
    track = Image.new("RGBA", (x1 - x0, h), (255, 255, 255, 70))
    blit(canvas, track, x0, y)
    fw = int((x1 - x0) * k)
    if fw > 2:
        ss = SS(fw, h, 2)
        ss.rrect((0, 0, fw, h), h / 2, fill=th["accent"] + (255,))
        blit(canvas, ss.finish(), x0, y)


# ------------------------------------------------------------------ timeline
def build_events(specs, th, tmap, total):
    """specs: clip['graphics'] list; tmap(src_t)->out time"""
    events = []
    for g in specs:
        typ = g["type"]
        if "at_clip" in g:
            t0 = float(g["at_clip"])
        else:
            t0 = tmap(float(g["at"]))
        dur = float(g.get("dur", 4.5 if typ in ("pyramid", "tree", "steps") else 2.0))
        dur = max(0.5, min(dur, total - t0 - 0.05))
        if dur <= 0.4:
            continue
        if typ == "pyramid":
            events.append(Pyramid(t0, dur, th, g["labels"], g.get("highlight"), g.get("title", "")))
        elif typ == "tree":
            events.append(OrgTree(t0, dur, th, g["tree"], g.get("highlight"), g.get("title", "")))
        elif typ == "steps":
            events.append(Steps(t0, dur, th, g["labels"], g.get("title", "")))
        elif typ == "keyword":
            events.append(Keyword(t0, dur, th, g["text"], g.get("sub", ""), g.get("y", 430), g.get("size", 150)))
        elif typ == "stat":
            events.append(Stat(t0, dur, th, g["value"], g.get("suffix", ""), g.get("label", ""),
                               g.get("prefix", ""), g.get("y", 560)))
        elif typ == "emoji":
            e = EmojiPop(t0, dur, th, g["char"], g.get("x", 0.5), g.get("y", 0.3), g.get("size", 240))
            if e.ok:
                events.append(e)
            else:
                print(f"  ! emoji {g['char']!r} not renderable, skipped")
        else:
            print(f"  ! unknown graphic type {typ!r}, skipped")
    return events
