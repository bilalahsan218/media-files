"""NullMotion moves for the Zamzam documentary style.

Every animation from the NullMotion library (github.com/blixvip/NullMotion, MIT) rebuilt in pure
Python on top of ir_doc.py, in the house palette: lavender desk, white paper, deep purple ink,
lilac highlighter, gold accents. No people, ever: avatars are ink stars, movers are dots.

Two layers:
  1. Primitives: GSAP-style eases, tw() tweens, put_fx() (scaleX/Y, blur, skew, rotation),
     mask_rise, wipe_in, glint, ripple, typing dots, caret, dust, scan beam, orbit ring, corners,
     meter, draw_path, count-up, paper pills and cards.
  2. Scene builders (each returns f(lt) -> RGBA frame, same contract as ir_doc scenes):
     manifesto_title, kinetic_scene, blur_reveal_scene, card_stack_scene, three_step_scene,
     morph_scene, hub_scene, bars_scene, timeline_scene, list_scene, search_scene, chat_scene,
     fan_scene, end_scene_nm.  Transitions: LIFT, ZOOM, PUSH_UP (plus ir_doc's WHIP_R/WHIP_L/flash).
The preset each one comes from is named in its docstring (nullmotion/presets/<id>/index.html).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from ir_doc import *   # noqa: F401,F403  (W, H, palette, fonts, paper, put, T, etc.)

# =====================================================================================
# 1. Eases (GSAP names) and tweens
# =====================================================================================
def _pin_(x): return 0.0 if x <= 0 else (1.0 if x >= 1 else x)
def _pow(n, mode):
    if mode == "in": return lambda x: x ** n
    if mode == "out": return lambda x: 1 - (1 - x) ** n
    return lambda x: (2 ** (n - 1)) * x ** n if x < .5 else 1 - (-2 * x + 2) ** n / 2
def _back(c, mode):
    if mode == "in": return lambda x: (c + 1) * x ** 3 - c * x ** 2
    if mode == "out": return lambda x: 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
    c2 = c * 1.525
    return lambda x: ((2 * x) ** 2 * ((c2 + 1) * 2 * x - c2)) / 2 if x < .5 else ((2 * x - 2) ** 2 * ((c2 + 1) * (x * 2 - 2) + c2) + 2) / 2
def _expo(mode):
    if mode == "in": return lambda x: 0 if x == 0 else 2 ** (10 * x - 10)
    if mode == "out": return lambda x: 1 if x == 1 else 1 - 2 ** (-10 * x)
    return expo_io
def _sine(mode):
    if mode == "in": return lambda x: 1 - math.cos(x * math.pi / 2)
    if mode == "out": return lambda x: math.sin(x * math.pi / 2)
    return lambda x: -(math.cos(math.pi * x) - 1) / 2
_EC = {}
def E(name="power3.out"):
    """GSAP ease by name: none, power1-4.(in|out|inOut), expo.*, sine.*, back.*(c), steps(n)."""
    if name in _EC: return _EC[name]
    if name in ("none", "linear"): f = lambda x: x
    elif name.startswith("steps"):
        n = int(name[6:-1]); f = lambda x, n=n: math.floor(x * n) / n
    else:
        fam, _, mode = name.partition(".")
        arg = None
        if "(" in mode: mode, arg = mode[:-1].split("("); arg = float(arg)
        mode = mode or "out"
        if fam.startswith("power"): f = _pow(int(fam[5:]) + 1, mode)
        elif fam == "expo": f = _expo(mode)
        elif fam == "sine": f = _sine(mode)
        elif fam == "back": f = _back(arg if arg is not None else 1.7, mode)
        else: raise ValueError(name)
    _EC[name] = f; return f
def tw(lt, t0, d, ease="power3.out"):
    """Eased progress 0..1 of a tween starting at t0 lasting d seconds."""
    return E(ease)(_pin_((lt - t0) / d)) if d > 0 else float(lt >= t0)
def lerp(a, b, k): return a + (b - a) * k
def yoyo(lt, t0, d, repeats=1, ease="sine.inOut"):
    """0 -> 1 -> 0 ... like GSAP yoyo:true, repeat:n. Returns 0..1."""
    if lt < t0: return 0.0
    n = (lt - t0) / d
    if n >= repeats + 1: return float((repeats + 1) % 2)
    i = int(n); f = n - i; v = E(ease)(f)
    return v if i % 2 == 0 else 1 - v

# =====================================================================================
# 2. Sprite helpers
# =====================================================================================
def put_fx(layer, spr, cx, cy, sx=1.0, sy=None, alpha=1.0, rot=0.0, blur=0.0, skew=0.0, origin="center"):
    """put() with separate scaleX/scaleY, gaussian blur (px), skewY (deg) and a transform origin
    ("center" | "bottom" | "left" | "top"). (cx, cy) is where the ORIGIN point lands."""
    sy = sx if sy is None else sy
    if alpha <= .004 or sx <= .005 or sy <= .005: return
    s = spr
    if blur > .4:
        p = int(blur * 2.5) + 2
        big = Image.new("RGBA", (s.width + 2 * p, s.height + 2 * p), (0, 0, 0, 0)); big.alpha_composite(s, (p, p))
        s = premul_blur(big, blur)
    if abs(skew) > .05:
        t = math.tan(math.radians(skew)); ex = int(abs(t) * s.width) + 2
        s = s.transform((s.width, s.height + ex), Image.AFFINE, (1, 0, 0, -t, 1, 0 if t > 0 else -ex), Image.BICUBIC)
    if abs(sx - 1) > 1e-3 or abs(sy - 1) > 1e-3:
        s = s.resize((max(1, int(s.width * sx)), max(1, int(s.height * sy))), Image.BICUBIC)
    if rot: s = s.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < .999: s = s.copy(); s.putalpha(s.getchannel("A").point(lambda v: int(v * alpha)))
    ox = {"left": s.width / 2}.get(origin, 0); oy = {"bottom": -s.height / 2, "top": s.height / 2}.get(origin, 0)
    put(layer, s, cx + ox, cy + oy)
def premul_blur(im, r):
    """Gaussian blur without dark fringes (premultiplied alpha)."""
    a = np.asarray(im).astype("float32"); al = a[..., 3:] / 255; a[..., :3] *= al
    b = Image.fromarray(np.clip(a, 0, 255).astype("uint8"), "RGBA").filter(ImageFilter.GaussianBlur(r))
    o = np.asarray(b).astype("float32"); al = np.maximum(o[..., 3:] / 255, 1e-3)
    o[..., :3] = o[..., :3] / al; return Image.fromarray(np.clip(o, 0, 255).astype("uint8"), "RGBA")
def alpha_mul(spr, a):
    if a >= .999: return spr
    s = spr.copy(); s.putalpha(s.getchannel("A").point(lambda v: int(v * a))); return s

def TW(text, f, col, ar=False, pad=8):
    """Text sprite on a FULL line box (ascent+descent), so words in a row share a baseline.
    Use instead of T() when words are animated one by one."""
    asc, desc = f.getmetrics(); kw = dict(direction="rtl", language="ar") if ar else {}
    w = int(f.getlength(text, **kw)) + pad * 2; h = asc + desc + pad * 2
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).text((pad, pad), text, font=f, fill=255, **kw)
    im = Image.new("RGBA", (w, h), col + (255,)); im.putalpha(m); return im

def word_row(text, f, col, cx, cy, gold=None, gap=None, maxw=None):
    """Lay out a line of words centred on (cx, cy). Returns [(sprite, centre_x, centre_y)].
    gold: a word (or tuple of words) drawn in GOLD."""
    ws = text.split(); gap = gap if gap is not None else f.getlength(" ")
    gold = (gold,) if isinstance(gold, str) else (gold or ())
    sp = [TW(w, f, GOLD if w.strip(".,?!:;“”\"'") in gold else col) for w in ws]
    tot = sum(s.width - 16 for s in sp) + gap * (len(sp) - 1); x = cx - tot / 2; out = []
    for s in sp: out.append((s, x + (s.width - 16) / 2, cy)); x += s.width - 16 + gap
    return out

def fit_font(lines, maker, maxw=940, start=150, floor=70):
    """Largest size (<= start) at which every line fits maxw. maker(size) -> font."""
    s = start
    while s > floor and max(maker(s).getlength(l) for l in lines) > maxw: s -= 4
    return s

def wrap(text, f, maxw):
    ws, lines, cur = text.split(), [], ""
    for w in ws:
        t = (cur + " " + w).strip()
        if f.getlength(t) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

# ---------- shapes ----------
def rounded(w, h, r, fill, outline=None, width=0, ss=2):
    """Anti-aliased rounded rectangle sprite."""
    w, h = max(2, int(w)), max(2, int(h))
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), int(r * ss), fill=fill, outline=outline, width=int(width * ss))
    return im.resize((w, h), Image.LANCZOS)
def disc(r, fill, ss=3):
    im = Image.new("RGBA", (int(r * 2 * ss), int(r * 2 * ss)), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((0, 0, im.width - 1, im.height - 1), fill=fill)
    return im.resize((int(r * 2), int(r * 2)), Image.LANCZOS)
def ring(r, col, width=4, dash=None, rot=0, ss=2):
    """Circle outline; dash=(on_deg, off_deg) for a dashed orbit; rot in degrees."""
    S = int((r + width) * 2 * ss) + 4; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    bb = (S / 2 - r * ss, S / 2 - r * ss, S / 2 + r * ss, S / 2 + r * ss)
    if dash:
        a = rot
        while a < rot + 360: d.arc(bb, a, a + dash[0], fill=col, width=int(width * ss)); a += dash[0] + dash[1]
    else: d.ellipse(bb, outline=col, width=int(width * ss))
    return im.resize((S // ss, S // ss), Image.LANCZOS)
def star8(R, col=INK, inner=.76, ss=3):
    """Eight-point star (the house mark; also used as the 'avatar' instead of any person)."""
    S = int(R * 2 * ss) + 4; im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(im).polygon(star_poly(S / 2, S / 2, R * ss, 0, inner), fill=col + (255,))
    return im.resize((S // ss, S // ss), Image.LANCZOS)

def pill(text, f, fg=PAPER, bg=INK, padx=58, pady=30, outline=None, ar=False):
    """Pill button/tag. Default: deep purple pill with paper text (the NullMotion 'obsidian pill')."""
    t = TW(text, f, fg, ar=ar); w, h = t.width - 16 + padx * 2, t.height - 16 + pady * 2
    im = rounded(w, h, h / 2, bg + (255,), outline + (255,) if outline else None, 3 if outline else 0)
    im.alpha_composite(t, (int((w - t.width) / 2), int((h - t.height) / 2))); return im
def icon_tile(size=84, col=INK, bg=LILAC):
    """Rounded lilac square with an ink eight-point star (replaces app icons / notification icons)."""
    im = rounded(size, size, size * .26, bg + (255,)); s = star8(size * .3, col)
    im.alpha_composite(s, ((size - s.width) // 2, (size - s.height) // 2)); return im
def card(w, h, seed, tape_rot=None):
    """Torn paper card with optional tape on top (ready for page_out)."""
    return paper(int(w), int(h), seed)

# =====================================================================================
# 3. Primitive moves
# =====================================================================================
def mask_rise(L, spr, cx, cy, k, travel=1.15, skew=0.0, blur=0.0, scale=1.0, alpha=None):
    """Line-mask reveal (03 slide-showcase, 26 manifesto title-word): the sprite slides up from below
    an invisible line clipped to its own box. k 0..1 (already eased)."""
    if k <= 0: return
    s = spr
    if skew or blur or abs(scale - 1) > 1e-3:
        tmp = Image.new("RGBA", (int(s.width * 1.3), int(s.height * 1.3)), (0, 0, 0, 0))
        put_fx(tmp, s, tmp.width / 2, tmp.height / 2, scale, scale, 1, 0, blur, skew)
        s = tmp.crop(((tmp.width - spr.width) // 2, (tmp.height - spr.height) // 2,
                      (tmp.width + spr.width) // 2, (tmp.height + spr.height) // 2))
    dy = int((1 - k) * travel * s.height)
    if dy >= s.height: return
    vis = s.crop((0, 0, s.width, s.height - dy))
    a = k if alpha is None else alpha
    x0, y0 = cx - s.width / 2, cy - s.height / 2
    put(L, alpha_mul(vis, min(1, a * 1.5)), x0 + vis.width / 2, y0 + dy + vis.height / 2)

def wipe_in(L, spr, x, y, k, from_right=False):
    """clip-path inset wipe, left to right (drafts 'logo' word). Top-left anchored. English only."""
    if k <= 0: return
    w = max(1, int(spr.width * min(1, k)))
    crop = spr.crop((spr.width - w, 0, spr.width, spr.height)) if from_right else spr.crop((0, 0, w, spr.height))
    L.alpha_composite(crop, (int(x + (spr.width - w if from_right else 0)), int(y)))

def glint(spr, k, col=(255, 255, 255), width=.22, strength=.55, angle=18):
    """Moving sheen across a sprite, masked by its alpha (01 cta-pill, 12 blur-reveal sweep, 19 bezel).
    k 0..1 = sweep position (use tw(..., 'power2.inOut'))."""
    if k <= 0 or k >= 1: return spr
    w, h = spr.size; xx = np.arange(w)[None, :] + np.arange(h)[:, None] * math.tan(math.radians(angle))
    pos = (-width + k * (1 + 2 * width)) * w
    band = np.exp(-((xx - pos) / (width * w * .5)) ** 2) * strength
    a = np.asarray(spr).astype("float32"); m = a[..., 3:] / 255
    a[..., :3] = a[..., :3] * (1 - band[..., None] * m) + np.array(col, "float32") * band[..., None] * m
    return Image.fromarray(np.clip(a, 0, 255).astype("uint8"), "RGBA")

def ripple(L, cx, cy, k, r_max=260, col=INK, width=6):
    """Press ripple (18 cta-click): ring expands, fades .5 -> 0. k already eased."""
    if k <= 0 or k >= 1: return
    rg = ring(max(2, r_max * k), col + (int(255 * .5 * (1 - k)),), width)
    put(L, rg, cx, cy)

def press(lt, t0, dip=.9):
    """Scale for a button press: dip in .12s (power2.in), spring back .35s (back.out(2.2))."""
    if lt < t0: return 1.0
    if lt < t0 + .12: return lerp(1, dip, tw(lt, t0, .12, "power2.in"))
    return lerp(dip, 1, tw(lt, t0 + .12, .35, "back.out(2.2)"))

def typing_dots(L, cx, cy, lt, t0, t1, col=GREY, r=11, gap=34):
    """Three bouncing dots (07 chat-sim): y -13 yoyo, stagger .13, until t1."""
    if not (t0 <= lt < t1): return
    k = tw(lt, t0, .3, "back.out(2)")
    bub = rounded(gap * 2 + r * 2 + 64, r * 2 + 50, (r * 2 + 50) / 2, LILAC + (255,))
    put_fx(L, bub, cx, cy, k, k)
    for i in range(3):
        ph = ((lt - t0 - .15 - i * .13) / .4)
        dy = -13 * abs(math.sin(math.pi * ph / 2)) if ph > 0 else 0
        put_fx(L, disc(r, col + (255,)), cx + (i - 1) * gap, cy + dy, k)

def caret(L, x, y, h, lt, t0=0, col=INK, w=5):
    """Blinking caret, steps(1), 0.5s on / 0.5s off."""
    if lt < t0 or int((lt - t0) / .5) % 2: return
    ImageDraw.Draw(L).rectangle((int(x), int(y), int(x + w), int(y + h)), fill=col + (255,))

def typed_chars(text, f, col, k):
    """Typewriter by CHARACTER count (NullMotion style, crisper than a crop). English only."""
    n = int(round(len(text) * _pin_(k)))
    return TW(text[:n], f, col) if n else None

def dust(L, lt, seed=5, n=26, col=LILAC, area=(80, 260, W - 80, 1650), rise=110, t0=0.0, fade_in=.7):
    """Floating specks drifting up with a slight sway (27 HUD dust, 26 manifesto particles)."""
    r = random.Random(seed); k = tw(lt, t0, fade_in, "power2.out")
    if k <= 0: return
    d = ImageDraw.Draw(L)
    for i in range(n):
        x0, y0 = r.uniform(area[0], area[2]), r.uniform(area[1], area[3]); sz = r.uniform(2.5, 6.5)
        ph = r.uniform(0, 6.28); sp = r.uniform(.6, 1.2)
        x = x0 + math.sin(lt * .8 * sp + ph) * 10 + ((i % 5) - 2) * 3 * lt / 7
        y = y0 - rise * sp * (lt / 7)
        a = int(255 * k * (.35 + .4 * ((i % 4) / 3)))
        c = (GOLD if i % 7 == 0 else col) + (a,)
        d.ellipse((x - sz, y - sz, x + sz, y + sz), fill=c)

def scan_beam(L, lt, t0, dur=5.5, col=LILAC, y0=200, y1=1700, h=220, peak=.55):
    """Soft horizontal light band sweeping down the frame (27 HUD scanBeam, power2.inOut)."""
    k = tw(lt, t0, dur, "power2.inOut")
    if k <= 0 or k >= 1: return
    a = peak * min(1, (lt - t0) / .4) * min(1, (t0 + dur - lt) / .42)
    y = lerp(y0, y1, k); band = np.exp(-((np.arange(int(h * 2)) - h) / (h * .45)) ** 2) * a * 255
    strip = Image.new("RGBA", (W, int(h * 2)), col + (0,))
    strip.putalpha(Image.fromarray(np.repeat(band[:, None], W, 1).astype("uint8")))
    L.alpha_composite(strip, (0, int(y - h)))

def orbit_ring(L, cx, cy, r, lt, speed=58, col=GREY, alpha=.35, dash=(14, 10), width=3, k=1.0):
    """Slowly rotating dashed orbit (22 kinetic orbit, 26 manifesto orbit-field, 27 HUD rings)."""
    if k <= 0: return
    put(L, ring(r, col + (int(255 * alpha * k),), width, dash, rot=lt * speed), cx, cy, .9 + .1 * k)

def corners(L, x0, y0, x1, y1, k, col=GREY, arm=54, width=5):
    """HUD corner brackets that scale in (27 HUD .corner)."""
    if k <= 0: return
    d = ImageDraw.Draw(L); a = arm * k; c = col + (int(255 * min(1, k * 1.4)),)
    for (x, y, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line((x, y, x + sx * a, y), fill=c, width=width); d.line((x, y, x, y + sy * a), fill=c, width=width)

def meter(L, x, y, w, h, k, col=INK, track=LILAC):
    """Rounded progress meter filling left to right (26 manifesto meter, 27 HUD meter-fill)."""
    put(L, rounded(w, h, h / 2, track + (255,)), x + w / 2, y + h / 2)
    if k > .01: put(L, rounded(max(h, w * k), h, h / 2, col + (255,)), x + max(h, w * k) / 2, y + h / 2)

def rule_overshoot(L, x0, x1, y, lt, t0, col=GOLD, th=9):
    """Gold rule that overshoots to 110% then settles (26 manifesto sub-rule)."""
    if lt < t0: return
    k = lerp(0, 1.1, tw(lt, t0, .6, "expo.out")) if lt < t0 + .6 else lerp(1.1, 1, tw(lt, t0 + .6, .3, "power3.inOut"))
    xe = x0 + (x1 - x0) * k; d = ImageDraw.Draw(L)
    d.polygon([(x0, y), (xe, y - 3), (xe, y + th - 3), (x0, y + th)], fill=col + (255,))

def draw_path(L, pts, k, col=INK, width=6, dash=None):
    """Draw a polyline up to fraction k of its length (16 line-growth curve, 09 links, 27 network paths)."""
    if k <= 0 or len(pts) < 2: return None
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]; tot = sum(seg); left = tot * min(1, k)
    d = ImageDraw.Draw(L); end = pts[0]
    for i, s in enumerate(seg):
        if left <= 0: break
        f = min(1, left / s) if s else 1; a = pts[i]; b = (a[0] + (pts[i + 1][0] - a[0]) * f, a[1] + (pts[i + 1][1] - a[1]) * f)
        if dash:
            n = max(1, int(math.dist(a, b) / sum(dash)))
            for j in range(n + 1):
                t0, t1 = j * sum(dash) / max(1, math.dist(a, b)), (j * sum(dash) + dash[0]) / max(1, math.dist(a, b))
                if t0 >= 1: break
                t1 = min(1, t1); d.line((lerp(a[0], b[0], t0), lerp(a[1], b[1], t0), lerp(a[0], b[0], t1), lerp(a[1], b[1], t1)), fill=col + (255,), width=width)
        else: d.line((a[0], a[1], b[0], b[1]), fill=col + (255,), width=width)
        end = b; left -= s
    return end

def count_to(lt, t0, d, value, ease="power3.out"):
    """Integer that counts up to value (13 compare-bars values, 26 metric cards)."""
    return int(round(value * tw(lt, t0, d, ease)))

def bob(lt, t0, amp=8, period=1.1):
    """Idle float (24 showreel phone, 15 tile): sine yoyo offset in px."""
    return 0 if lt < t0 else -amp * math.sin(math.pi * ((lt - t0) / period))

# =====================================================================================
# 4. Scene builders
# =====================================================================================
def _kicker(L, text_spr, lt, t0=.1, y=400):
    k = tw(lt, t0, .7, "expo.out")
    if k > 0: put(L, text_spr, W / 2, y - 40 * (1 - k), 1, k)

def manifesto_title(eyebrow, lines, gold_word=None, arabic=None, sub=None, atmos=True, y0=760):
    """Title hook (26 null-manifesto + 03 slide-showcase).
    Eyebrow rises from a mask; each headline WORD rises out of its line mask with skewY 7 -> 0,
    scale 1.075 -> 1, blur 15 -> 0 (power4.out .9, stagger .08); gold rule overshoots under the key word;
    Arabic fades up out of a blur; subcopy words rise with blur (stagger .045). Done by about 2.6s."""
    size = fit_font(lines, lambda s: ID("Black", s), 940, 150)
    F = ID("Black", size); lh = int(size * 1.08)
    eb = hcat([star8(13, GOLD), TW(eyebrow, MONO(28), GREY)], 14) if eyebrow else None
    ys = [y0 + i * lh for i in range(len(lines))]
    rows = [word_row(l, F, INK, W / 2, ys[i]) for i, l in enumerate(lines)]
    ar = TW(arabic, FA(104), GREY, ar=True) if arabic else None
    subrow = word_row(sub, LOI(44), GREY, W / 2, ys[-1] + (300 if ar else 150)) if sub else []
    gold = None
    if gold_word:
        for i, l in enumerate(lines):
            if gold_word in l:
                x0 = W / 2 - F.getlength(l) / 2 + F.getlength(l[:l.index(gold_word)])
                gold = (x0, x0 + F.getlength(gold_word), ys[i] + size * .52); break
    def f(lt):
        L = desk()
        if atmos: dust(L, lt, 11, 22)
        if eb: mask_rise(L, eb, W / 2, ys[0] - lh * .78, tw(lt, .1, .9, "expo.out"), 1.3)
        n = 0
        for i, row in enumerate(rows):
            for spr, cx, cy in row:
                t0 = .35 + i * .12 + n * .08; k = tw(lt, t0, .9, "power4.out"); n += 1
                if k > 0:
                    a = _pin_((lt - t0) / .45)
                    mask_rise(L, spr, cx, cy, k, 1.18, skew=7 * (1 - k), blur=15 * (1 - k), scale=lerp(1.075, 1, k), alpha=a)
        tg = .35 + n * .08 + .45
        if gold: rule_overshoot(L, gold[0], gold[1], gold[2], lt, tg)
        if ar:
            ka = tw(lt, tg + .2, .7, "power3.out")
            if ka > 0: put_fx(L, ar, W / 2, ys[-1] + 175 + 26 * (1 - ka), 1, None, ka, 0, 10 * (1 - ka))
        for j, (spr, cx, cy) in enumerate(subrow):
            t0 = tg + .4 + j * .045; k = tw(lt, t0, .53, "power4.out")
            if k > 0: mask_rise(L, spr, cx, cy, k, 1.24, blur=5 * (1 - k), alpha=_pin_((lt - t0) / .3))
        return L
    f.cover_time = .35 + (sum(len(r) for r in rows)) * .08 + 1.4 + (.9 if subrow else 0)
    return f

def kinetic_scene(left, right, key, index=None, micro=None, key_ar=False, y=820):
    """One-word emphasis (22 kinetic-headline). A lilac guide rule draws, an index label rises, the left
    word slides in from the left and the right word from the right (x +-112, rot +-1.2, blur 8), then the
    KEY word lands in a purple pill with squash-and-stretch (scaleX .93->1.08->1, scaleY 1.06->.95->1),
    a contact shadow spreads, a gold spark crosses the pill and a sheen sweeps it. Orbit ring drifts."""
    FS = fit_font([left, right], lambda s: ID("Black", s), 900, 140)
    Lw, Rw = TW(left, ID("Black", FS), INK), TW(right, ID("Black", FS), INK)
    P = pill(key, FA(84) if key_ar else ID("Black", 96), PAPER, INK, 70, 26, ar=key_ar)
    idx = TW(index, MONO(28), GREY) if index else None
    mic = TW(micro, LOI(42), GREY) if micro else None
    yl, yr, yp = y, y + FS * 1.05, y + FS * 1.05 + 70 + P.height / 2 + FS * .5
    sh = disc(P.width * .45, INK + (60,)).resize((int(P.width * .9), 26))
    def f(lt):
        L = desk()
        glow = tw(lt, 0, .72, "power3.out")
        if glow > 0: put_fx(L, disc(330, LILAC + (110,)), W / 2 + 11 * tw(lt, 1.35, 1.8, "sine.inOut"), yp - 60, lerp(.72, .86, glow), None, glow, 0, 40)
        orbit_ring(L, W / 2 - 9 * tw(lt, 1.35, 1.8, "sine.inOut"), yp - 40, 430, lt, 20, k=tw(lt, .04, .82, "power3.inOut"))
        g = tw(lt, .08, .68, "power3.inOut")
        if g > 0: ImageDraw.Draw(L).line((W / 2 - 420 * g, y - FS * .75, W / 2 + 420 * g, y - FS * .75), fill=LILAC + (255,), width=4)
        if idx:
            k = tw(lt, .16, .4, "power2.out")
            if k > 0: put(L, idx, W / 2, y - FS * .75 - 44 + 10 * (1 - k), 1, k)
        k = tw(lt, .2, .72, "power4.out")
        if k > 0: put_fx(L, Lw, W / 2 - 112 * (1 - k), yl + 18 * (1 - k), 1, None, k, -1.2 * (1 - k), 8 * (1 - k))
        k = tw(lt, .29, .72, "power4.out")
        if k > 0: put_fx(L, Rw, W / 2 + 112 * (1 - k), yr - 18 * (1 - k), 1, None, k, 1.2 * (1 - k), 8 * (1 - k))
        if lt >= .45:
            if lt < .82:
                k = tw(lt, .45, .43, "power3.out"); sx, sy, dy, bl, a = lerp(.93, 1.08, k), lerp(1.06, .95, k), lerp(12, -4, k), 6 * (1 - k), k
            else:
                k = tw(lt, .82, .34, "back.out(1.55)"); sx, sy, dy, bl, a = lerp(1.08, 1, k), lerp(.95, 1, k), lerp(-4, 0, k), 0, 1
            ks = tw(lt, .48, .62, "power3.out")
            put_fx(L, sh, W / 2, yp + P.height / 2 + 22 - 8 * (1 - ks), lerp(.55, 1, ks), 1, ks)
            pp = glint(P, tw(lt, 1.22, .76, "power3.inOut"), strength=.45)
            put_fx(L, pp, W / 2, yp + dy, sx, sy, a, 0, bl)
            if 1.22 <= lt < 1.92:
                sp = tw(lt, 1.23, .68, "power3.inOut"); sa = 1 - tw(lt, 1.72, .2, "sine.out")
                put(L, star8(16, GOLD), W / 2 + lerp(-P.width * .45, P.width * .45, sp), yp - 6 * sp - P.height * .55, 1, sa, rot=lt * 120)
        if mic:
            k = tw(lt, .76, .42, "power2.out")
            if k > 0: put(L, mic, W / 2, yp + P.height / 2 + 110 + 9 * (1 - k), 1, k)
        return L
    return f

def blur_reveal_scene(kicker, word, meaning=None, translit=None, ref=None, word_ar=True, takeaway=None):
    """Key-word reveal (12 blur-reveal). A paper plate drops in (back.out(1.3)); the word sits blurred
    (20px, 35% opacity) until a lilac light sweep crosses the plate and it sharpens; the plate's shadow
    blooms lilac. Then transliteration, meaning and the gold reference rise. Arabic is never cropped."""
    K = TW(kicker, ID("Black", 76), INK) if kicker else None
    WD = TW(word, FA(190), INK, ar=True) if word_ar else TW(word, ID("Black", 150), INK)
    PW, PH = 880, 640; PLATE = paper(PW, PH, 33)
    TR = TW(translit, MONO(34), GREY) if translit else None
    ME = [TW(l, LOI(46), INK) for l in wrap(meaning, LOI(46), 760)] if meaning else []
    RF = TW(ref, MONO(26), GOLD) if ref else None
    TK = TW(takeaway, ID("Bold", 50), INK) if takeaway else None
    cy = 960
    def f(lt):
        L = desk(); dust(L, lt, 4, 16)
        if K: _kicker(L, K, lt, .1, 380)
        k = tw(lt, .2, .8, "back.out(1.3)")
        if k <= 0: return L
        pg = PLATE.copy()
        sw = tw(lt, 1.8, 1.1, "power2.inOut")
        if 0 < sw < 1:
            xx = np.arange(PW)[None, :] + np.arange(PH)[:, None] * .35; pos = lerp(-200, PW + 200, sw)
            band = (np.exp(-((xx - pos) / 90) ** 2) * 150).astype("uint8")
            ov = Image.new("RGBA", (PW, PH), LILAC + (0,)); ov.putalpha(Image.fromarray(band))
            m = pg.getchannel("A"); ov.putalpha(Image.fromarray(np.minimum(np.asarray(ov.getchannel("A")), np.asarray(m))))
            pg.alpha_composite(ov)
        s = tw(lt, 2.0, .9, "power2.out")
        put_fx(pg, WD, PW / 2, 250, 1, None, lerp(.35, 1, s), 0, 20 * (1 - s))
        if TR:
            kk = tw(lt, 2.7, .5, "power3.out")
            if kk > 0: put(pg, TR, PW / 2, 420 + 14 * (1 - kk), 1, kk)
        for i, m_ in enumerate(ME):
            kk = tw(lt, 2.9 + i * .15, .55, "power3.out")
            if kk > 0: put(pg, m_, PW / 2, 490 + i * 58 + 16 * (1 - kk), 1, kk)
        if RF:
            kk = tw(lt, 3.3, .5, "power2.out")
            if kk > 0: put(pg, RF, PW / 2, PH - 50, 1, kk)
        bloom = tw(lt, 2.3, .8, "sine.out")
        if bloom > 0: put_fx(L, disc(PW * .55, LILAC + (int(200 * bloom),)), W / 2, cy + 20 * (1 - k), 1.15, .95, 1, 0, 50)
        put_fx(L, page_out(pg, -1.0), W / 2, cy + 70 * (1 - k), lerp(.9, 1, k), None, _pin_(k * 1.6))
        tp = tape(170, 46, 9).rotate(-6, expand=True); put(L, tp, W / 2, cy - PH / 2 - 4 + 70 * (1 - k), 1, _pin_(k * 1.6))
        if TK:
            kk = tw(lt, 3.8, .55, "power3.out")
            if kk > 0: put(L, TK, W / 2, 1460 + 26 * (1 - kk), 1, kk)
        return L
    return f

def card_stack_scene(title, items, start=.6, gap=.7, highlight_index=None, ref=None):
    """Notification stack (06 notification, 24 showreel-notify). Taped index cards with an ink-star
    icon drop in one after another (y -90, scale .95, back.out(1.4)). items: [{label, text, ref}].
    Optional lilac highlighter sweeps under one card's text afterwards."""
    TI = TW(title, ID("Black", fit_font([title], lambda s: ID("Black", s), 940, 84)), INK)
    CW = 920; cards = []
    for i, it in enumerate(items):
        lines = wrap(it["text"], LO(38), CW - 210)[:3]; ch = 120 + 50 * len(lines)
        pg = paper(CW, ch, 50 + i); ic = icon_tile(84); pg.alpha_composite(ic, (40, 36))
        if it.get("label"): pg.alpha_composite(TW(it["label"], MONO(24), GREY), (150, 26))
        sprs = [TW(l, LO(38), INK) for l in lines]
        if it.get("ref"): pg.alpha_composite(TW(it["ref"], MONO(22), GOLD), (CW - 40 - TW(it["ref"], MONO(22), GOLD).width, 26))
        cards.append((pg, sprs, ch))
    tot = sum(c[2] for c in cards) + 34 * (len(cards) - 1); y = 960 - tot / 2 + 40; pos = []
    for c in cards: pos.append(y + c[2] / 2); y += c[2] + 34
    RF = TW(ref, MONO(26), GOLD) if ref else None
    def f(lt):
        L = desk(); _kicker(L, TI, lt, .1, min(420, pos[0] - cards[0][2] / 2 - 90))
        for i, ((pg, sprs, ch), cy) in enumerate(zip(cards, pos)):
            t0 = start + i * gap; k = tw(lt, t0, .7, "back.out(1.4)")
            if k <= 0: continue
            p = pg.copy()
            if highlight_index == i:
                hk = tw(lt, start + len(cards) * gap + .3, .5)
                for j, s in enumerate(sprs): highlight(p, 150, 82 + j * 50 + 26, s.width - 20, 46, _pin_(hk * 1.3 - j * .3))
            for j, s in enumerate(sprs): p.alpha_composite(s, (142, 72 + j * 50))
            put_fx(L, page_out(p, (-1) ** i * .8, 14), W / 2, cy - 90 * (1 - k), lerp(.95, 1, k), None, _pin_(k * 2))
            put(L, tape(150, 42, i + 3).rotate(8 * (-1) ** i, expand=True), W / 2 + 330 * (-1) ** i, cy - ch / 2 - 90 * (1 - k), 1, _pin_(k * 2))
        if RF:
            kk = tw(lt, start + len(cards) * gap + .2, .5)
            if kk > 0: put(L, RF, W / 2, min(1560, pos[-1] + cards[-1][2] / 2 + 70), 1, kk)
        return L
    return f

def three_step_scene(title, steps, ref=None):
    """Triple sequence (02 three-step), stacked for 9:16. Each card rises from scaleY .9 at its bottom
    edge (power4.out 1.0, stagger .45) and its progress bar grows (expo.out .9). The stack drifts up
    14px (sine.inOut) during the hold. steps: [(num, head, desc)]."""
    TI = TW(title, ID("Black", fit_font([title], lambda s: ID("Black", s), 940, 84)), INK)
    CW, CH = 900, 300; cards = []
    for i, (num, head, desc) in enumerate(steps):
        pg = paper(CW, CH, 60 + i); pg.alpha_composite(TW(num, MONO(30), GOLD), (50, 34))
        pg.alpha_composite(TW(head, ID("Bold", 58), INK), (50, 74))
        for j, l in enumerate(wrap(desc, LO(34), CW - 100)[:2]): pg.alpha_composite(TW(l, LO(34), GREY), (50, 152 + j * 44))
        cards.append(pg)
    ys = [640 + i * (CH + 38) for i in range(len(steps))]
    RF = TW(ref, MONO(26), GOLD) if ref else None
    def f(lt):
        L = desk(); _kicker(L, TI, lt, .05, 400); dr = -14 * tw(lt, 2, 4, "sine.inOut")
        for i, (pg, cy) in enumerate(zip(cards, ys)):
            t0 = .4 + i * .45; k = tw(lt, t0, 1.0, "power4.out")
            if k <= 0: continue
            p = pg.copy(); bk = tw(lt, t0 + .35, .9, "expo.out")
            if bk > 0:
                d = ImageDraw.Draw(p); d.rounded_rectangle((50, CH - 26, 50 + (CW * .62) * bk, CH - 17), 5, fill=INK + (255,))
            put_fx(L, page_out(p, 0, 14), W / 2, cy + CH / 2 + 50 + 36 * (1 - k) + dr, 1, lerp(.9, 1, k), _pin_(k * 1.8), 0, 0, 0, "bottom")
        if RF:
            kk = tw(lt, .4 + len(cards) * .45 + .6, .5)
            if kk > 0: put(L, RF, W / 2, ys[-1] + CH + 70 + dr, 1, kk)
        return L
    return f

def morph_scene(pill_text, title, rows, ref=None, takeaway=None, rows_ar=False):
    """Morph panel (04 morph-panel). A purple pill rises (expo.out), its label fades, then the pill
    morphs (power4.inOut 1.4s) into a paper page; title and rows slide in (x -40, stagger .12)."""
    P = pill(pill_text, ID("Bold", 46)); PW0, PH0 = P.width, P.height; PW1 = 900
    TI = TW(title, ID("Black", 60), INK)
    RS = [TW(r, FA(56), INK, ar=True) if rows_ar else TW(r, LOI(48), INK) for r in rows]
    PH1 = 60 + TI.height + 30 + sum(s.height + 6 for s in RS) + (100 if ref else 50)
    RF = TW(ref, MONO(26), GOLD) if ref else None
    TK = TW(takeaway, ID("Bold", 50), INK) if takeaway else None
    PAGE = paper(PW1, int(PH1), 77); cy = 900
    def f(lt):
        L = desk(); dust(L, lt, 8, 14)
        k = tw(lt, .2, .8, "expo.out")
        if k <= 0: return L
        m = tw(lt, 1.5, 1.4, "power4.inOut")
        if m <= 0:
            pa = 1 - tw(lt, 1.5, .4, "power2.in")   # label fades as the morph begins
            body = rounded(PW0, PH0, PH0 / 2, INK + (255,)); body.alpha_composite(alpha_mul(P, pa))
            put_fx(L, page_out(body, 0, 12), W / 2, cy + 60 * (1 - k), lerp(.9, 1, k), None, _pin_(k * 1.5))
            return L
        w, h = lerp(PW0, PW1, m), lerp(PH0, PH1, m); r = lerp(PH0 / 2, 14, m)
        col = tuple(int(lerp(a, b, m)) for a, b in zip(INK, PAPER))
        body = rounded(w, h, r, col + (255,))
        pk = tw(lt, 2.6, .6, "power2.out")
        if pk > 0:
            pg = PAGE.copy(); y = 60
            kk = tw(lt, 2.7, .7, "power3.out"); onto(pg, TI, 60, y, kk, 24); y += TI.height + 30
            for i, s in enumerate(RS):
                kk = tw(lt, 2.9 + i * .12, .6, "power3.out")
                if kk > 0: pg.alpha_composite(alpha_mul(s, kk), (int((PW1 - 60 - s.width) if rows_ar else 60 - 40 * (1 - kk)), int(y)))
                y += s.height + 6
            if RF: onto(pg, RF, 60, PH1 - 76, tw(lt, 3.1 + len(RS) * .12, .5), 10)
            put(L, page_out(body, 0, 14), W / 2, cy, 1, 1 - pk)
            put(L, page_out(pg, 0, 16), W / 2, cy, 1, pk)
        else:
            put(L, page_out(body, 0, 14), W / 2, cy)
        if TK:
            kk = tw(lt, 3.6 + len(RS) * .12, .55, "power3.out")
            if kk > 0: put(L, TK, W / 2, min(1520, cy + PH1 / 2 + 110) + 26 * (1 - kk), 1, kk)
        return L
    return f

def hub_scene(title, hub, nodes, hub_ar=False, ref=None, cy=990, R=360, node_gap=.32):
    """Grid network (09 grid-network + 27 HUD hub). Faint map grid fades in (scale 1.1 -> 1), the ink
    hub pops (back.out(1.7)), dashed links draw to 4-6 paper pills that pop in turn (back.out(1.8)),
    the hub pulses (1.06 yoyo) and a dashed orbit turns around it. Labels never collide: keep each
    node under ~14 characters."""
    TI = TW(title, ID("Black", fit_font([title], lambda s: ID("Black", s), 940, 84)), INK)
    HB = disc(132, INK + (255,)); HT = TW(hub, FA(78) if hub_ar else ID("Black", 44 if len(hub) > 7 else 56), PAPER, ar=hub_ar)
    NS = [pill(n, ID("Bold", 38), INK, PAPER, 34, 20, outline=LILAC) for n in nodes]; N = len(NS)
    pos = [(W / 2 + R * math.cos(math.radians(-90 + i * 360 / N)), cy + R * 1.04 * math.sin(math.radians(-90 + i * 360 / N))) for i in range(N)]
    RF = TW(ref, MONO(26), GOLD) if ref else None
    GRID = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(GRID)
    for x in range(30, W, 90): g.line((x, 250, x, 1650), fill=LILAC + (120,), width=1)
    for y in range(250, 1650, 90): g.line((0, y, W, y), fill=LILAC + (120,), width=1)
    def f(lt):
        L = desk(); gk = tw(lt, 0, 1.0, "power2.out")
        if gk > 0: put(L, GRID, W / 2, H / 2, lerp(1.1, 1, gk), gk)
        _kicker(L, TI, lt, .1, 380)
        orbit_ring(L, W / 2, cy, 190, lt, 25, INK, .3, k=tw(lt, .6, .8))
        for i, (p, s) in enumerate(zip(pos, NS)):
            t0 = .9 + i * node_gap; lk = tw(lt, t0, .5, "power2.inOut")
            if lk > 0:
                sh = .6 + .4 * yoyo(lt, 2.2 + i * .05, .52, 2) if lt > 2.2 else 1
                a = (W / 2 + (p[0] - W / 2) * .37, cy + (p[1] - cy) * .37)
                draw_path(L, [a, p], lk, tuple(int(lerp(c, 255, .3 * (1 - sh))) for c in GREY), 4, (14, 10))
            nk = tw(lt, t0 + .2, .6, "back.out(1.8)")
            if nk > 0: put(L, page_out(s, 0, 10), p[0], p[1], nk, _pin_(nk * 2))
        hk = tw(lt, .3, .8, "back.out(1.7)")
        if hk > 0:
            pulse = 1 + .06 * yoyo(lt, 1.6 + N * node_gap * .5, .9, 2)
            put(L, with_shadow(HB, 14, (6, 10), .6), W / 2, cy, hk * pulse)
            put(L, HT, W / 2, cy, hk * pulse)
        if RF:
            kk = tw(lt, 1.1 + N * node_gap, .5)
            if kk > 0: put(L, RF, W / 2, min(1580, cy + R + 160), 1, kk)
        return L
    return f

def bars_scene(title, bars, caption=None, ref=None, unit=""):
    """Compare bars (13 compare-bars + 15 bar-3d). A paper chart card rises (power4.out), bars grow
    from the baseline in a stagger with values counting up, a caption pill rises (expo.out).
    bars: [{label, value, pct (0-1 of max height), key: bool}] 2 to 4. Check pct = value / max."""
    TI = TW(title, ID("Black", fit_font([title], lambda s: ID("Black", s), 940, 84)), INK)
    CW, CH = 900, 860; CARD = paper(CW, CH, 91); d = ImageDraw.Draw(CARD)
    base = CH - 150
    for gy in range(base, 90, -110): d.line((60, gy, CW - 60, gy), fill=LILAC + (255,), width=2)
    n = len(bars); bw = min(190, (CW - 160) / n - 50); xs = [80 + (CW - 160) * (i + .5) / n for i in range(n)]
    for x, b in zip(xs, bars):
        lab = TW(b["label"], MONO(26), GREY); CARD.alpha_composite(lab, (int(x - lab.width / 2), base + 26))
    CP = pill(caption, ID("Bold", 40)) if caption else None
    RF = TW(ref, MONO(26), GOLD) if ref else None
    cy = 960
    def f(lt):
        L = desk(); _kicker(L, TI, lt, .05, 400)
        k = tw(lt, 0, .8, "power4.out")
        if k <= 0: return L
        pg = CARD.copy(); dd = ImageDraw.Draw(pg)
        for i, (x, b) in enumerate(zip(xs, bars)):
            t0 = .45 + i * .17; bk = tw(lt, t0, .7 + .25 * i, "power4.out")
            hgt = (base - 140) * b["pct"] * bk
            if hgt > 1: dd.rounded_rectangle((x - bw / 2, base - hgt, x + bw / 2, base), 12, fill=(INK if b.get("key") else LILAC) + (255,))
            vk = tw(lt, t0 + .25, .5, "power3.out")
            if vk > 0:
                v = TW(f"{b.get('prefix', '')}{count_to(lt, t0, .7 + .25 * i, b['value'])}{b.get('suffix', unit)}", ID("Black", 56), INK)
                put(pg, v, x, base - hgt - 46 + 14 * (1 - vk), 1, vk)
        put(L, page_out(pg, 0, 16), W / 2, cy + 60 * (1 - k), lerp(.97, 1, k), _pin_(k * 1.6))
        if CP:
            ck = tw(lt, .45 + n * .17 + .8, .7, "expo.out")
            if ck > 0: put(L, page_out(CP, 0, 10), W / 2, cy + CH / 2 + 80 + 30 * (1 - ck), lerp(.96, 1, ck), ck)
        if RF:
            kk = tw(lt, .45 + n * .17 + 1.2, .5)
            if kk > 0: put(L, RF, W / 2, min(1580, cy + CH / 2 + (170 if CP else 70)), 1, kk)
        return L
    return f

def timeline_scene(title, events, ref=None, x_line=230):
    """Line growth as a vertical timeline (16 line-growth). The spine draws down (power2.inOut);
    each marker pops (back.out(1.8)) exactly as the line passes it, and its label slides in.
    events: [(label, text)] 3 to 5 (label e.g. a year or a place in mono; text one short line)."""
    TI = TW(title, ID("Black", fit_font([title], lambda s: ID("Black", s), 940, 84)), INK)
    n = len(events); y0, y1 = 560, 560 + (n - 1) * 230
    rows = [(TW(a, MONO(28), GOLD), [TW(l, LO(40), INK) for l in wrap(b, LO(40), 700)[:2]]) for a, b in events]
    ys = [lerp(y0, y1, i / max(1, n - 1)) for i in range(n)]; DUR = .6 + .55 * n
    RF = TW(ref, MONO(26), GOLD) if ref else None
    def f(lt):
        L = desk(); _kicker(L, TI, lt, .05, 400)
        k = tw(lt, .5, DUR, "power2.inOut")
        if k > 0: draw_path(L, [(x_line, y0 - 40), (x_line, y1 + 40)], k, LILAC, 8)
        head = lerp(y0 - 40, y1 + 40, k)
        for (lab, ls), y in zip(rows, ys):
            if head < y: continue
            pass_t = .5 + DUR * ((y - y0 + 40) / (y1 - y0 + 80))
            mk = tw(lt, pass_t, .5, "back.out(1.8)")
            put(L, with_shadow(disc(22, INK + (255,)), 6, (3, 5), .5), x_line, y, mk)
            sk = tw(lt, pass_t + .1, .6, "power3.out")
            if sk > 0:
                put(L, lab, x_line + 70 + lab.width / 2 - 30 * (1 - sk), y - 38, 1, sk)
                for j, s in enumerate(ls): put(L, s, x_line + 70 + s.width / 2 - 30 * (1 - sk), y + 12 + j * 50, 1, sk)
        if RF:
            kk = tw(lt, .5 + DUR + .3, .5)
            if kk > 0: put(L, RF, W / 2, min(1580, y1 + 150), 1, kk)
        return L
    return f

def list_scene(title, rows, me=None, ref=None, note=None):
    """Leaderboard / connector list (14 leaderboard + 21 connector-list). Paper strips slide in from
    the left (x -70, power4.out, stagger .16), their right-hand value slides from x +16; then a lilac
    highlight snaps behind row `me`, pulses, and an ink marker circle draws around its label.
    rows: [(left_text, right_text)]; left may be Arabic if you pass ('ar', text)."""
    TI = TW(title, ID("Black", fit_font([title], lambda s: ID("Black", s), 940, 84)), INK)
    RW, RH = 900, 124; n = len(rows); y0 = 960 - (n - 1) * (RH + 22) / 2
    sprs = []
    for i, (a, b) in enumerate(rows):
        la = TW(a[1], FA(58), INK, ar=True) if isinstance(a, tuple) else TW(a, ID("Bold", 48), INK)
        sprs.append((paper(RW, RH, 120 + i), TW(f"{i + 1:02d}", MONO(28), GOLD), la, TW(b, MONO(28), GREY) if b else None))
    NT = TW(note, LOI(42), GREY) if note else None; RF = TW(ref, MONO(26), GOLD) if ref else None
    t_hl = .45 + n * .16 + .4
    def f(lt):
        L = desk(); _kicker(L, TI, lt, .05, min(400, y0 - 120))
        for i, (pg, num, la, rb) in enumerate(sprs):
            y = y0 + i * (RH + 22); k = tw(lt, .15 + i * .16, .7, "power4.out")
            if k <= 0: continue
            p = pg.copy()
            if me == i and lt > t_hl:
                hk = tw(lt, t_hl, .35, "power2.out"); glow = .6 + .4 * yoyo(lt, t_hl + .05, .4, 1)
                ov = rounded(RW - 20, RH - 20, 16, LILAC + (int(200 * hk * glow),)); p.alpha_composite(ov, (10, 10))
            p.alpha_composite(num, (28, (RH - num.height) // 2)); p.alpha_composite(la, (120, (RH - la.height) // 2))
            if rb:
                rk = tw(lt, .45 + i * .16, .5, "power4.out")
                if rk > 0: p.alpha_composite(alpha_mul(rb, rk), (int(RW - 40 - rb.width + 16 * (1 - rk)), (RH - rb.height) // 2))
            if me == i: marker_circle(p, 120 + la.width / 2, RH / 2, la.width / 2 + 26, RH / 2 - 10, tw(lt, t_hl + .3, .55), width=5)
            put(L, page_out(p, 0, 12), W / 2 - 70 * (1 - k), y, 1, _pin_(k * 1.5))
        if NT:
            kk = tw(lt, t_hl + .9, .55, "power3.out")
            if kk > 0: put(L, NT, W / 2, y0 + n * (RH + 22) + 40 + 20 * (1 - kk), 1, kk)
        if RF:
            kk = tw(lt, t_hl + 1.1, .5)
            if kk > 0: put(L, RF, W / 2, min(1580, y0 + n * (RH + 22) + (120 if NT else 40)), 1, kk)
        return L
    return f

def search_scene(mark, query, results=None, me=None, type_dur=1.7):
    """Search typing (20 search-typing + 08 prompt-bar). A headline rises, a paper search bar rises,
    the query types itself character by character with a blinking caret, the search button presses,
    and result cards rise beneath (the `me` result gets a lilac highlight). Hook device only:
    results must be real, sourced lines."""
    MK = TW(mark, ID("Black", fit_font([mark], lambda s: ID("Black", s), 940, 96)), INK)
    BW, BH = 920, 128; BAR = rounded(BW, BH, BH / 2, PAPER + (255,), LILAC + (255,), 3)
    BTN = disc(40, INK + (255,)); FQ = LO(42)
    RS = [paper(860, 110, 140 + i) for i in range(len(results or []))]
    RT = [TW(r, LO(36), INK) for r in (results or [])]
    by = 760
    def f(lt):
        L = desk(); k = tw(lt, .1, .7, "power3.out")
        if k > 0: put(L, MK, W / 2, 520 + 30 * (1 - k), 1, k)
        bk = tw(lt, .35, .7, "power3.out")
        if bk <= 0: return L
        bar = BAR.copy(); q = typed_chars(query, FQ, INK, tw(lt, .9, type_dur, "none"))
        qx = 60
        if q: bar.alpha_composite(q, (qx, (BH - q.height) // 2))
        if lt < .9 + type_dur + .3: caret(bar, qx + (q.width - 14 if q else 0), BH / 2 - 26, 52, lt, .85)
        sc = press(lt, .9 + type_dur + .15)
        put(bar, BTN, BW - 70, BH / 2, sc); put(bar, ring(14, PAPER + (255,), 4), BW - 74, BH / 2 - 4, sc)
        ImageDraw.Draw(bar).line((BW - 64, BH / 2 + 6, BW - 54, BH / 2 + 16), fill=PAPER + (255,), width=5)
        put(L, with_shadow(bar, 14, (6, 10), .5), W / 2, by + 26 * (1 - bk), 1, bk)
        ripple(L, W / 2 + BW / 2 - 70, by, tw(lt, .9 + type_dur + .2, .7, "power2.out"), 150)
        for i, (pg, t) in enumerate(zip(RS, RT)):
            rk = tw(lt, .9 + type_dur + .5 + i * .18, .6, "power3.out")
            if rk <= 0: continue
            p = pg.copy()
            if me == i: highlight(p, 50, 55, t.width, 50, tw(lt, .9 + type_dur + 1.2 + len(RS) * .18, .5))
            p.alpha_composite(t, (50, (110 - t.height) // 2))
            put(L, page_out(p, 0, 10), W / 2, by + 170 + i * 130 + 20 * (1 - rk), 1, rk)
        return L
    return f

def chat_scene(ask_label, ask, answer_label, answer, ref=None, saw=True):
    """Chat sim (07 chat-sim), documentary version. A question card pops in on the right
    (back.out(1.4)); an ink-star 'avatar' (never a face) appears with three bouncing dots; then the
    answer card types out line by line with a caret and the gold reference rises.
    answer_label with saw=True renders e.g. 'THE PROPHET ﷺ SAID' with the honorific in Amiri gold."""
    AL = TW(ask_label, MONO(24), GREY); AQ = [TW(l, LOI(42), INK) for l in wrap(ask, LOI(42), 640)]
    AW = max([s.width for s in AQ] + [AL.width]) + 80; AH = 70 + len(AQ) * 54 + 30
    ASK = rounded(AW, AH, 28, PAPER + (255,), LILAC + (255,), 3)
    ASK.alpha_composite(AL, (40, 26))
    for j, s in enumerate(AQ): ASK.alpha_composite(s, (40, 62 + j * 54))
    ab = answer_label.split("ﷺ") if saw and "ﷺ" in answer_label else None
    LAB = SAW(ab[0].strip(), MONO(24), GREY, ab[1].strip() or None) if ab else TW(answer_label, MONO(24), GREY)
    AN = [TW(l, LOI(46), INK) for l in wrap(answer, LOI(46), 720)]
    PW = 820; PH = 100 + len(AN) * 60 + (80 if ref else 30); PAGE = paper(PW, PH, 151)
    RF = TW(ref, MONO(24), GOLD) if ref else None
    AV = disc(42, INK + (255,)); AV.alpha_composite(star8(20, PAPER), (22, 22))
    ya, yb = 640, 640 + AH / 2 + 90
    t_ans = 2.7; per = 1.6 / max(1, len(AN))
    def f(lt):
        L = desk(); k = tw(lt, .3, .55, "back.out(1.4)")
        if k > 0: put_fx(L, page_out(ASK, 0, 12), W - 80 - AW / 2, ya + 46 * (1 - k), lerp(.96, 1, k), None, _pin_(k * 2))
        av = tw(lt, 1.0, .25)
        if av > 0: put(L, AV, 110, yb + 30, 1, av)
        typing_dots(L, 270, yb + 30, lt, 1.1, t_ans)
        if lt >= t_ans:
            pg = PAGE.copy(); onto(pg, LAB, 50, 36, tw(lt, t_ans, .3), 8)
            for j, s in enumerate(AN):
                typed_on(pg, s, 50, 86 + j * 60, (lt - t_ans - .05 - j * per) / per)
            last = min(len(AN) - 1, int((lt - t_ans - .05) / per)); kk = (lt - t_ans - .05 - last * per) / per
            if lt < t_ans + 1.9 and last >= 0:
                caret(pg, 50 + AN[last].width * _pin_(kk) + 4, 92 + last * 60, 46, lt, t_ans)
            if RF: onto(pg, RF, 50, PH - 62, tw(lt, t_ans + 1.8, .45), 8)
            put(L, page_out(pg, 0, 14), 180 + PW / 2, yb + 10 + PH / 2, 1, 1)
        return L
    return f

def fan_scene(front_cards, caption=None, flip_back=None):
    """Icon stack rise (27 icon-stack-rise). Three cards rise together from below with an overshoot
    (power4.out then back.out(1.28)), the front card squashes, flips on its vertical axis (shown as a
    scaleX turn) to its back face, the side cards fan out left and right (back.out(1.38)), all three
    bob once, and the caption rises. front_cards: three RGBA sprites (polaroids, cards); flip_back:
    optional sprite for the master's back face."""
    A, M, B = front_cards; BK = flip_back
    CP = TW(caption, ID("Bold", 52), INK) if caption else None
    cy = 900; SH = disc(300, INK + (70,)).resize((520, 46))
    def f(lt):
        L = desk(); dust(L, lt, 21, 14)
        if lt < 1.161: sy = lerp(1120, -28, tw(lt, .14, 1.02, "power4.out"))
        else: sy = lerp(-28, 0, tw(lt, 1.161, .239, "back.out(1.28)"))
        shk = tw(lt, .2, .96, "power3.out"); put(L, SH, W / 2, cy + 330, lerp(.36, .58, shk) + .42 * tw(lt, 2.18, .5), lerp(.66, 1, shk))
        fan = [tw(lt, 1.74, .72, "back.out(1.38)"), tw(lt, 1.84, .72, "back.out(1.38)")]
        b1 = bob(lt, 3.35, 7, .38) if lt < 4.11 else 0
        put(L, A, W / 2 - 300 * fan[0], cy + lerp(38, 12, fan[0]) + sy + b1, lerp(.94, 1, fan[0]), _pin_((lt - .14) / .08), rot=lerp(4, 2, fan[0]))
        put(L, B, W / 2 + 300 * fan[1], cy + lerp(76, 12, fan[1]) + sy + b1, lerp(.88, 1, fan[1]), _pin_((lt - .2) / .08), rot=lerp(-4, -2, fan[1]))
        face = M; scx = 1; scy = 1; my = 0
        if 1.4 <= lt < 1.55: k = tw(lt, 1.4, .13, "power2.out"); scx, scy, my = 1 + .035 * k, 1 - .025 * k, 18 * k
        elif 1.55 <= lt < 1.89: k = tw(lt, 1.55, .339, "power3.in"); scx, my = max(.02, math.cos(math.radians(88 * k))), lerp(18, -12, k)
        elif 1.89 <= lt < 2.25:
            k = tw(lt, 1.891, .359, "power3.out"); scx, my = max(.02, math.cos(math.radians(88 * (1 - k)))), -12
            face = BK or M
        elif lt >= 2.25:
            face = BK or M; my = lerp(-12, 0, tw(lt, 2.251, .309, "back.out(1.24)"))
        put_fx(L, face, W / 2, cy + sy + my + b1, scx, scy, _pin_((lt - .14) / .08), 2 * (1 - tw(lt, 1.55, .34)))
        gk = tw(lt, 1.48, .42) * (1 - tw(lt, 2.43, .6))
        if gk > 0: put_fx(L, disc(160, PAPER + (int(160 * gk),)), W / 2, cy - 60 + sy, 1.1, None, 1, 0, 30)
        if CP:
            ck = tw(lt, 2.6, .6, "power3.out")
            if ck > 0: put(L, CP, W / 2, cy + 440 + 26 * (1 - ck), 1, ck)
        return L
    return f

def end_scene_nm(series="HISTORY  ·  DID YOU KNOW?"):
    """House end card with NullMotion moves (drafts 'logo' + 01 cta-pill + 18 cta-click).
    The eight-point star pops (scale 0, rot -40, back.out(1.8)); ISLAMIC REELS wipes in left to right;
    the gold rule overshoots; the series label rises; the 'Follow for more' pill rises (expo.out),
    a glint sweeps it, it is pressed with a ripple; the share line settles. Same words as end_scene()."""
    BR = TW("ISLAMIC REELS", ID("Black", 104), INK); ST = star8(46, INK)
    SUB = TW(series, MONO(30), GREY); CTA = pill("Follow for more", ID("Bold", 50)); SHR = TW("Share it. The reward is yours too.", LOI(40), GREY)
    by = 860
    def f(lt):
        L = desk(); dust(L, lt, 31, 18)
        k = tw(lt, .05, .55, "back.out(1.8)")
        if k > 0: put(L, ST, W / 2, by - 150, k, 1, rot=-40 * (1 - k))
        wipe_in(L, BR, W / 2 - BR.width / 2, by - BR.height / 2, tw(lt, .3, .6, "power2.out"))
        rule_overshoot(L, W / 2 - 330, W / 2 + 330, by + 75, lt, .7)
        kk = tw(lt, .9, .5, "power3.out")
        if kk > 0: put(L, SUB, W / 2, by + 150 + 20 * (1 - kk), 1, kk)
        ck = tw(lt, 1.1, .85, "expo.out")
        if ck > 0:
            cp = glint(CTA, tw(lt, 1.7, .9, "power2.inOut"))
            put(L, with_shadow(cp, 14, (6, 12), .6), W / 2, by + 300 + 90 * (1 - ck), lerp(.96, 1, ck) * press(lt, 2.75, .92), _pin_(ck * 1.5))
            ripple(L, W / 2, by + 300, tw(lt, 2.8, .7, "power2.out"), 360)
        sk = tw(lt, 1.4, .6, "power3.out")
        if sk > 0: put(L, SHR, W / 2, by + 430 + 18 * (1 - sk), 1, sk)
        return L
    return f

# =====================================================================================
# 5. Transitions (use alongside ir_doc's WHIP_R / WHIP_L / flash)
# =====================================================================================
def _desk_rgba(): return Image.new("RGBA", (W, H), DESK + (255,))
def LIFT(A, Bf, q):
    """Manifesto exit: A lifts 46px and fades (power3.in), B rises 46px into place (power3.out)."""
    out = _desk_rgba(); qa = E("power3.in")(_pin_(q / .55)); qb = E("power3.out")(_pin_((q - .35) / .65))
    if qa < 1: put(out, alpha_mul(A, 1 - qa), W / 2, H / 2 - 46 * qa)
    if qb > 0: put(out, alpha_mul(Bf, qb), W / 2, H / 2 + 46 * (1 - qb))
    return out
def ZOOM(A, Bf, q):
    """Zoom-through: A scales up 8% with a blur and fades, B settles from 94% (expo.out)."""
    out = _desk_rgba(); qa = E("power2.in")(_pin_(q / .55)); qb = E("expo.out")(_pin_((q - .3) / .7))
    if qa < 1: put_fx(out, A, W / 2, H / 2, 1 + .08 * qa, None, 1 - qa, 0, 8 * qa)
    if qb > 0: put(out, Bf, W / 2, H / 2, lerp(.94, 1, qb), qb)
    return out
def PUSH_UP(A, Bf, q):
    """Vertical whip: both frames slide up with motion blur (expo.inOut), like the whip pan."""
    e = expo_io(q); bl = 60 * math.sin(math.pi * e); out = _desk_rgba()
    out.alpha_composite(_shift_v(_vb(A, bl), int(-H * e))); out.alpha_composite(_shift_v(_vb(Bf, bl), int(H * (1 - e))))
    return out
def _vb(L, amt):
    if amt < 2: return L
    a = np.asarray(L).astype("float32"); a[..., :3] *= a[..., 3:] / 255; acc = np.zeros_like(a)
    for o in np.linspace(-amt / 2, amt / 2, 21).astype(int): acc += np.roll(a, o, axis=0)
    acc /= 21; al = np.maximum(acc[..., 3:], 1e-3); acc[..., :3] = acc[..., :3] * 255 / al
    return Image.fromarray(np.clip(acc, 0, 255).astype("uint8"), "RGBA")
def _shift_v(L, dy):
    out = new()
    if abs(dy) >= H: return out
    out.alpha_composite(L.crop((0, max(0, -dy), W, min(H, H - dy))), (0, max(0, dy))); return out
