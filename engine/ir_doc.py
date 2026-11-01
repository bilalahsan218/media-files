"""Islamic Reels documentary prop-style engine (the "Zamzam style").
Lavender desk, white paper props, deep purple ink, lilac highlighter, gold accents.
Pure Python: Pillow + numpy, piped to ffmpeg. 1080x1920 @ 30fps.
"""
import math, os, glob, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30

# ---------- brand palette ----------
DESK = (233, 227, 247)     # #E9E3F7 lavender background
PAPER = (255, 255, 255)    # #FFFFFF paper
INK = (59, 31, 110)        # #3B1F6E deep purple: text, pins, marker, stamp
PURPLE = INK
GREY = (107, 90, 146)      # #6B5A92 labels, secondary text
LILAC = (207, 195, 238)    # #CFC3EE highlighter, tape
GOLD = (201, 165, 92)      # #C9A55C sparingly: underlines, references, the honorific

# ---------- fonts ----------
def _find(patterns):
    for pat in patterns:
        hits = glob.glob(pat, recursive=True)
        if hits: return sorted(hits)[0]
    raise FileNotFoundError(f"font not found: {patterns}")
FONT_DIRS = ["/usr/share/fonts/**/", os.path.expanduser("~/fonts/**/"), "/home/claude/fonts/**/"]
def _f(name): return _find([d + name for d in FONT_DIRS])
_CACHE = {}
def _font(key, path_name, size):
    k = (key, size)
    if k not in _CACHE: _CACHE[k] = ImageFont.truetype(_f(path_name), size)
    return _CACHE[k]
def ID(weight, s): return _font("id" + weight, f"InterDisplay-{weight}.otf", s)   # headlines: Black / Bold
def LO(s): return _font("lo", "Lora-Variable.ttf", s)                             # document body
def LOI(s): return _font("loi", "Lora-Italic-Variable.ttf", s)                    # quotes
def MONO(s): return _font("mono", "DejaVuSansMono-Bold.ttf", s)                   # labels, references
def FA(s): return _font("amiri", "amiri-arabic-700-normal.woff2", s)              # Arabic (needs raqm)

# ---------- easing ----------
def c01(x): return max(0.0, min(1.0, x))
def p(t, s, d): return c01((t - s) / d)
def eo(x): return 1 - (1 - x) ** 3
def eo5(x): return 1 - (1 - x) ** 5
def eio(x): return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def expo_io(x):
    if x <= 0: return 0
    if x >= 1: return 1
    return 2 ** (20 * x - 10) / 2 if x < .5 else (2 - 2 ** (-20 * x + 10)) / 2
def back(x, c1=1.7):
    c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

# ---------- text sprites ----------
def text_mask(txt, f, track=0, ar=False, pad=6):
    kw = dict(direction="rtl", language="ar") if ar else {}
    if track:
        ws = [f.getlength(c) for c in txt]; asc, desc = f.getmetrics()
        w = int(sum(ws) + track * (len(txt) - 1)) + pad * 2; h = asc + desc + pad * 2
        m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m); x = pad
        for c, cw in zip(txt, ws): d.text((x, pad), c, font=f, fill=255); x += cw + track
        bb = m.getbbox(); return m.crop((bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad))
    bb = f.getbbox(txt, **kw)
    m = Image.new("L", (bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2), 0)
    ImageDraw.Draw(m).text((pad - bb[0], pad - bb[1]), txt, font=f, fill=255, **kw)
    return m
def T(s, f, col, track=0, ar=False):
    """Solid-colour text sprite. ar=True for Arabic (RTL shaping)."""
    m = text_mask(s, f, track, ar); im = Image.new("RGBA", m.size, col + (255,)); im.putalpha(m); return im
def hcat(parts, gap=10):
    """Join sprites in a row, vertically centred. Use for mixed scripts, e.g. 'THE PROPHET' + ﷺ in Amiri."""
    hh = max(q.height for q in parts); ww = sum(q.width for q in parts) + gap * (len(parts) - 1)
    out = Image.new("RGBA", (ww, hh), (0, 0, 0, 0)); x = 0
    for q in parts: out.alpha_composite(q, (x, (hh - q.height) // 2)); x += q.width + gap
    return out
def SAW(prefix, font, col=GREY, suffix=None):
    """'THE PROPHET ﷺ SAID' style label with the honorific typeset in Amiri gold."""
    parts = [T(prefix, font, col), T("ﷺ", FA(int(font.size * 1.3)), GOLD)]
    if suffix: parts.append(T(suffix, font, col))
    return hcat(parts, 8)

# ---------- compositing ----------
def new(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))
def put(layer, spr, cx, cy, scale=1.0, alpha=1.0, rot=0):
    """Paste sprite centred at (cx, cy) with scale/alpha/rotation; clips safely at edges."""
    if alpha <= .004 or scale <= .01: return
    s = spr
    if rot: s = s.rotate(rot, Image.BICUBIC, expand=True)
    if abs(scale - 1) > 1e-3: s = s.resize((max(1, int(s.width * scale)), max(1, int(s.height * scale))), Image.BICUBIC)
    if alpha < .999: s = s.copy(); s.putalpha(s.getchannel("A").point(lambda v: int(v * alpha)))
    x, y = int(cx - s.width / 2), int(cy - s.height / 2)
    x0, y0 = max(0, -x), max(0, -y); x1, y1 = min(s.width, layer.width - x), min(s.height, layer.height - y)
    if x1 <= x0 or y1 <= y0: return
    layer.alpha_composite(s.crop((x0, y0, x1, y1)), (x + x0, y + y0))
def onto(pg, spr, x, y, k=1.0, dy=18):
    """Fade-rise a sprite onto a page at top-left (x, y)."""
    if k <= 0: return
    s = spr
    if k < 1: s = spr.copy(); s.putalpha(s.getchannel("A").point(lambda v: int(v * k)))
    pg.alpha_composite(s, (int(x), int(y + dy * (1 - k))))
def typed_on(pg, spr, x, y, k):
    """Typewriter reveal, left to right (English only; fade Arabic with onto())."""
    if k <= 0: return
    w = max(1, int(spr.width * c01(k))); pg.alpha_composite(spr.crop((0, 0, w, spr.height)), (int(x), int(y)))

# ---------- desk, vignette, grain ----------
_yy, _xx = np.mgrid[0:H, 0:W]
_rng = np.random.default_rng(3)
_desk = np.array(DESK, dtype="float32") + (np.exp(-(((_xx - W * .5) / 700) ** 2 + ((_yy - H * .42) / 900) ** 2)) * 10)[..., None]
_desk += _rng.normal(0, 1.5, (H, W, 1)).astype("float32")
DESK_IMG = Image.fromarray(np.clip(_desk, 0, 255).astype("uint8")).convert("RGBA")
VIG = np.clip(1 - .12 * (((_xx - W / 2) / (W * .75)) ** 2 + ((_yy - H / 2) / (H * .7)) ** 2), .8, 1).astype("float32")
GRAIN = [_rng.normal(0, 3.5, (H, W, 1)).astype("float32") for _ in range(6)]
def desk(): return DESK_IMG.copy()

# ---------- props ----------
def paper(w, h, seed, col=PAPER, edge=6):
    """Torn-edge paper with faint stains and darker edges."""
    r = random.Random(seed); pts = []
    for x in range(0, w + 1, 18): pts.append((x, r.uniform(0, edge)))
    for y in range(0, h + 1, 18): pts.append((w - r.uniform(0, edge), y))
    for x in range(w, -1, -18): pts.append((x, h - r.uniform(0, edge)))
    for y in range(h, -1, -18): pts.append((r.uniform(0, edge), y))
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).polygon(pts, fill=255)
    g = np.random.default_rng(seed)
    base = np.array(col, dtype="float32")[None, None, :] + g.normal(0, 4, (h, w, 1))
    for _ in range(5):
        cx, cy, rr = g.uniform(0, w), g.uniform(0, h), g.uniform(80, 260)
        d = np.exp(-(((np.arange(w)[None, :] - cx) ** 2 + (np.arange(h)[:, None] - cy) ** 2) / (2 * rr * rr)))
        base -= (d * g.uniform(3, 6))[..., None] * np.array([.5, .7, .2])
    ed = np.minimum.reduce([np.arange(w)[None, :].repeat(h, 0), (w - np.arange(w))[None, :].repeat(h, 0),
                            np.arange(h)[:, None].repeat(w, 1), (h - np.arange(h))[:, None].repeat(w, 1)])
    base -= (np.clip(1 - ed / 40, 0, 1) * 8)[..., None] * np.array([.7, .8, .4])
    im = Image.fromarray(np.clip(base, 0, 255).astype("uint8")).convert("RGBA"); im.putalpha(m); return im
def with_shadow(im, blur=18, off=(10, 16), op=.6):
    """Soft purple drop shadow (props float above the desk)."""
    op *= .45; P = blur * 3
    out = Image.new("RGBA", (im.width + P * 2, im.height + P * 2), (0, 0, 0, 0))
    sh = Image.new("L", out.size, 0); sh.paste(im.getchannel("A").point(lambda v: v * op), (P + off[0], P + off[1]))
    out.paste(Image.new("RGBA", out.size, INK + (255,)), (0, 0), sh.filter(ImageFilter.GaussianBlur(blur)))
    out.alpha_composite(im, (P, P)); return out
def page_out(pg, rot=0, blur=20):
    out = with_shadow(pg, blur, (12, 18), .65)
    return out.rotate(rot, Image.BICUBIC, expand=True) if rot else out
def tape(w=170, h=46, seed=1):
    r = random.Random(seed); im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pts = [(0, r.uniform(0, 4))] + [(x, 0) for x in range(10, w - 10, 20)] + [(w, r.uniform(0, 4)), (w - r.uniform(0, 5), h)] + \
          [(x, h) for x in range(w - 10, 10, -20)] + [(r.uniform(0, 5), h)]
    d.polygon(pts, fill=(218, 208, 245, 190)); return im
def _pin():
    S = 4; im = Image.new("RGBA", (60 * S, 60 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((14 * S, 10 * S, 46 * S, 42 * S), fill=INK + (255,)); d.ellipse((20 * S, 15 * S, 30 * S, 25 * S), fill=(200, 185, 240, 220))
    return with_shadow(im.resize((60, 60), Image.LANCZOS), 5, (4, 6), .55)
PIN = _pin()
def stamp(text, col=INK, rot=-8):
    f = MONO(46); tw = int(f.getlength(text)) + 60
    im = Image.new("RGBA", (tw, 100), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((4, 4, tw - 4, 96), 12, outline=col + (255,), width=6); d.text((30, 22), text, font=f, fill=col + (255,))
    a = np.array(im.getchannel("A")).astype("float32") * np.random.default_rng(7).uniform(.55, 1, (100, tw))
    im.putalpha(Image.fromarray(a.astype("uint8"))); return im.rotate(rot, Image.BICUBIC, expand=True)
def polaroid(art, label, rot):
    w, h = art.width + 40, art.height + 120
    im = Image.new("RGBA", (w, h), PAPER + (255,)); im.alpha_composite(art, (20, 20))
    lt = T(label, MONO(26), INK); im.alpha_composite(lt, ((w - lt.width) // 2, art.height + 70 - lt.height // 2))
    return with_shadow(im.rotate(rot, Image.BICUBIC, expand=True), 14, (8, 12), .6)
def map_paper(w, h, seed, title):
    """Grid map paper with a title and compass star."""
    mp = paper(w, h, seed, (248, 245, 254)); d = ImageDraw.Draw(mp)
    for gx in range(60, w, 110): d.line((gx, 40, gx, h - 40), fill=(226, 218, 246, 255), width=1)
    for gy in range(60, h, 110): d.line((40, gy, w - 40, gy), fill=(226, 218, 246, 255), width=1)
    mp.alpha_composite(T(title, MONO(28), GREY, track=3), (60, 60))
    d.polygon(star_poly(w - 110, 120, 52, 0, .4), outline=GREY + (255,), width=3)
    n = T("N", MONO(28), GREY); mp.alpha_composite(n, (w - 110 - n.width // 2, 28)); return mp
def star_poly(cx, cy, R, rot=0, inner=.76):
    pts = []
    for i in range(16):
        rr = R if i % 2 == 0 else R * inner * math.cos(math.radians(22.5)); a = math.radians(rot + i * 22.5 - 90)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts

# ---------- marker / highlighter effects (draw on a page BEFORE its text for highlight) ----------
def highlight(L, x0, cy, w, h, k, col=LILAC, a=150):
    if k <= 0: return
    ov = Image.new("RGBA", L.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov); ww = w * eio(k)
    d.polygon([(x0 - 6, cy - h / 2 + 3), (x0 + ww + 6, cy - h / 2), (x0 + ww + 2, cy + h / 2), (x0 - 2, cy + h / 2 + 2)], fill=col + (a,))
    L.alpha_composite(ov)
def marker_circle(L, cx, cy, rx, ry, k, col=INK, width=7):
    if k <= 0: return
    S = 2; ov = Image.new("RGBA", (L.width * S, L.height * S), (0, 0, 0, 0)); d = ImageDraw.Draw(ov); sw = 400 * eio(k)
    d.arc(((cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S), -140, -140 + sw, fill=col + (255,), width=width * S)
    d.arc(((cx - rx - 6) * S, (cy - ry + 4) * S, (cx + rx + 4) * S, (cy + ry + 6) * S), -120, -120 + sw * .9, fill=col + (200,), width=(width - 3) * S)
    L.alpha_composite(ov.resize(L.size, Image.LANCZOS))
def underline(L, x0, x1, y, k, col=GOLD, th=9):
    if k <= 0: return
    d = ImageDraw.Draw(L); xe = x0 + (x1 - x0) * eio(k)
    d.polygon([(x0, y), (xe, y - 3), (xe, y + th - 3), (x0, y + th)], fill=col + (255,))
def tally(L, x0, y, n_done, k_last, col=INK):
    """Hand-drawn tally marks: 4 strokes, a slash, then more strokes."""
    d = ImageDraw.Draw(L)
    for j in range(n_done):
        tk = 1 if j < n_done - 1 else k_last
        if j % 5 < 4:
            x = x0 + (j // 5) * 200 + (j % 5) * 34; d.line((x, y, x + 4, y + 90 * tk), fill=col + (255,), width=8)
        else:
            bx = x0 + (j // 5) * 200; d.line((bx - 18, y + 65, bx - 18 + 140 * tk, y + 65 - 50 * tk), fill=col + (255,), width=8)

# ---------- transitions ----------
def hblur(L, amt):
    if amt < 2: return L
    a = np.asarray(L).astype("float32"); a[..., :3] *= a[..., 3:] / 255
    acc = np.zeros_like(a)
    for o in np.linspace(-amt / 2, amt / 2, 25).astype(int): acc += np.roll(a, o, axis=1)
    acc /= 25; al = np.maximum(acc[..., 3:], 1e-3); acc[..., :3] = acc[..., :3] * 255 / al
    return Image.fromarray(np.clip(acc, 0, 255).astype("uint8"), "RGBA")
def shift(L, dx):
    if abs(dx) >= W: return new()
    out = new(); out.alpha_composite(L.crop((max(0, -dx), 0, min(W, W - dx), H)), (max(0, dx), 0)); return out
def whip(A, Bf, q, dirn=1):
    e = expo_io(q); bl = 90 * math.sin(math.pi * e)
    out = Image.new("RGBA", (W, H), DESK + (255,))
    out.alpha_composite(shift(hblur(A, bl), int(-dirn * W * e))); out.alpha_composite(shift(hblur(Bf, bl), int(dirn * W * (1 - e))))
    return out
def flash(A, Bf, q):
    img = A if q < .5 else Bf; f = math.exp(-((q - .5) / .12) ** 2)
    return Image.blend(img.convert("RGB"), Image.new("RGB", (W, H), (255, 255, 255)), f * .85).convert("RGBA")
WHIP_R = lambda a, b, q: whip(a, b, q, 1)
WHIP_L = lambda a, b, q: whip(a, b, q, -1)

# ---------- standard scenes ----------
def title_scene(tag_text, lines, gold_word=None, arabic=None):
    """Taped scrap tag + slamming headline lines + optional gold underline under gold_word + optional Arabic."""
    tag = T(tag_text, MONO(26), INK); scrap = with_shadow(paper(tag.width + 70, 88, 12), 10, (6, 8), .6)
    sizes = [128 if len(s) <= 11 else (116 if len(s) <= 14 else 100) for s in lines]
    spr = [T(s, ID("Black", sz), INK) for s, sz in zip(lines, sizes)]
    ar = T(arabic, FA(110), GREY, ar=True) if arabic else None
    ys = [820 + i * 140 for i in range(len(lines))]
    def f(lt):
        L = desk(); k = eo5(p(lt, .15, .6))
        if k > 0:
            put(L, scrap.rotate(-3, Image.BICUBIC, expand=True), W / 2, 600 - 300 * (1 - k))
            put(L, tag.rotate(-3, Image.BICUBIC, expand=True), W / 2, 596 - 300 * (1 - k))
            put(L, tape(130, 40, 2).rotate(28, expand=True), W / 2 - scrap.width / 2 + 10, 566 - 300 * (1 - k))
        for i, s in enumerate(spr):
            kk = p(lt, .55 + i * .24, .35)
            if kk > 0: put(L, s, W / 2, ys[i], 1.6 - .6 * eo5(kk), c01(kk * 3))
        if gold_word:
            for i, line in enumerate(lines):
                if gold_word in line:
                    fnt = ID("Black", sizes[i]); x0 = W / 2 - fnt.getlength(line) / 2 + fnt.getlength(line[:line.index(gold_word)])
                    underline(L, x0, x0 + fnt.getlength(gold_word), ys[i] + 70, p(lt, 1.4, .45)); break
        if ar:
            k2 = eo5(p(lt, 1.8, .5))
            if k2 > 0: put(L, ar, W / 2, ys[-1] + 190 + 30 * (1 - k2), 1, k2)
        return L
    return f

_E = dict(brand=T("ISLAMIC REELS", ID("Black", 104), INK, track=2), cta=T("Follow for more", ID("Bold", 52), INK),
          sh=T("Share it. The reward is yours too.", LOI(40), GREY))
def end_scene(series="HISTORY  ·  DID YOU KNOW?"):
    sub = T(series, MONO(30), GREY)
    def f(lt):
        L = desk(); k = p(lt, .1, .4)
        if k > 0: put(L, _E["brand"], W / 2, 860, 1.4 - .4 * eo5(k), c01(k * 3))
        underline(L, W / 2 - 330, W / 2 + 330, 935, p(lt, .5, .45))
        for spr, y, st in ((sub, 1010, .8), (_E["cta"], 1140, 1.1), (_E["sh"], 1220, 1.4)):
            kk = eo5(p(lt, st, .5))
            if kk > 0: put(L, spr, W / 2, y + 30 * (1 - kk), 1, kk)
        return L
    return f

# ---------- renderer ----------
def render(scenes, starts, dur, trans, out, preview=None, pre=.25, win=(.25, .35), push=.03):
    """scenes: list of f(lt) -> RGBA frame. starts: scene start times. trans: len(scenes)-1 transition fns.
    preview: list of times -> saves PNGs next to `out` instead of rendering the video."""
    def frame(t):
        img = None
        for i in range(1, len(starts)):
            b = starts[i]
            if b - win[0] <= t < b + win[1]:
                q = (t - (b - win[0])) / sum(win)
                img = trans[i - 1](scenes[i - 1](t - starts[i - 1] + (0 if i == 1 else pre)), scenes[i](t - b + pre), q); break
        i = max(j for j in range(len(starts)) if starts[j] <= t)
        if img is None: img = scenes[i](t - starts[i] + (0 if i == 0 else pre))
        z = 1 + push * c01((t - starts[i]) / 6)   # slow documentary camera push
        if z > 1.001:
            sw, sh = int(W * z), int(H * z); img = img.resize((sw, sh), Image.BICUBIC).crop(((sw - W) // 2, (sh - H) // 2, (sw - W) // 2 + W, (sh - H) // 2 + H))
        arr = np.asarray(img.convert("RGB")).astype("float32") * VIG[..., None] + GRAIN[int(t * FPS) % 6]
        if t < .3: arr = arr * eo(t / .3) + np.array(DESK) * (1 - eo(t / .3))
        if t > dur - .45: arr = arr * eo((dur - t) / .45) + np.array(DESK) * (1 - eo((dur - t) / .45))
        return np.clip(arr, 0, 255).astype("uint8")
    if preview:
        base = os.path.splitext(out)[0]; paths = []
        for t in preview:
            pth = f"{base}_pv_{t}.png"; Image.fromarray(frame(t)).save(pth); paths.append(pth)
        return paths
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-maxrate", "14M", "-bufsize", "28M",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for n in range(int(dur * FPS)): ff.stdin.write(frame(n / FPS).tobytes())
    ff.stdin.close(); ff.wait(); return out
