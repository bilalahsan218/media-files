"""Viral moves for Islamic Reels (from the user's reference reels), in the house palette.

The references use: a small lead-in line over a BIG bold keyword; words that fill in as they are spoken;
a solid bar that wipes in before the word lands inside it; an icon that replaces a letter (the clock in
HOURS); an arc that sweeps around the hero object; a diagonal light sweep; a diagonal ribbon of repeating
text; a giant ghost word behind the hero; a hand-drawn marker loop; letters that build one by one; one word
that swells inside a sentence; a spotlight stage with a checker floor where a pawn becomes a king; a purple
hill/pedestal; floating icons; rim glow; tilted (perspective) planes; and a dark outro with the handle.

No people: heroes are objects, symbols, places, cards, pieces. Every function takes the scene-local time t
and its own start times, so cues can be tied to measured narration (WT/ON from ir_urdu).
Build on ir_motion (which imports ir_doc).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from ir_motion import *          # noqa: F401,F403
from ir_motion import _pin_

PURPLE = (124, 58, 237)          # vivid accent from the references; use sparingly (keywords, bars, hill)
PURPLE_D = (88, 36, 170)
VIOLET_L = (196, 170, 246)
STUDIO_TOP, STUDIO_BOT = (252, 251, 255), (226, 222, 238)

# =====================================================================================
# Backdrops
# =====================================================================================
_yy, _xx = np.mgrid[0:H, 0:W]
def _studio():
    g = np.exp(-(((_xx - W / 2) / (W * .62)) ** 2 + ((_yy - H * .36) / (H * .5)) ** 2))
    a = np.array(STUDIO_BOT, "float32") + (np.array(STUDIO_TOP, "float32") - np.array(STUDIO_BOT, "float32")) * g[..., None]
    top = np.clip(1 - _yy / (H * .28), 0, 1)[..., None] ** 2          # lilac haze at the top, as in the references
    a = a * (1 - .35 * top) + np.array(VIOLET_L, "float32") * .35 * top
    return Image.fromarray(np.clip(a, 0, 255).astype("uint8")).convert("RGBA")
STUDIO = _studio()
def studio(): return STUDIO.copy()

def stage_hill(L, k, top=1450, r=1000, col_top=PURPLE, col_bot=PURPLE_D):
    """Big purple dome rising from the bottom edge (its top at y=top): a pedestal for the hero object."""
    if k <= 0: return
    S = 2; hill = Image.new("RGBA", (int(r * 2 * S), int(r * 2 * S)), (0, 0, 0, 0)); d = ImageDraw.Draw(hill)
    for i in range(30):
        f = i / 29; c = tuple(int(lerp(a_, b_, f)) for a_, b_ in zip(col_top, col_bot))
        d.ellipse((f * r * .08 * S, f * r * .5 * S, (2 * r - f * r * .08) * S, 2 * r * S), fill=c + (255,))
    hill = hill.resize((int(r * 2), int(r * 2)), Image.LANCZOS)
    put(L, hill, W / 2, top + r + 520 * (1 - E("power3.out")(_pin_(k))))

def checker_floor(L, k, horizon=1060, rows=10, cols=8, c1=(250, 248, 255), c2=PURPLE_D, z_far=7.0, spread=1.7):
    """Perspective checkerboard from the horizon to the bottom edge (the chess stage); k slides it up.
    Rows shrink toward the horizon (1/z), columns converge to the centre."""
    if k <= 0: return
    S = 2; fw, fh = W * S, (H - horizon) * S
    fl = Image.new("RGBA", (fw, fh), (0, 0, 0, 0)); d = ImageDraw.Draw(fl)
    def proj(X, z):                     # X: world across (-cols/2..cols/2), z: depth 1 (near) .. z_far
        y = fh * (1 / z - 1 / z_far) / (1 - 1 / z_far); x = fw / 2 + X / z * fw / cols * spread
        return (x, y)
    zs = [1 + (z_far - 1) * (i / rows) ** 1.6 for i in range(rows + 1)]
    for r_ in range(rows):
        for c_ in range(-cols, cols):
            col = c1 if (r_ + c_) % 2 == 0 else c2
            d.polygon([proj(c_, zs[r_]), proj(c_ + 1, zs[r_]), proj(c_ + 1, zs[r_ + 1]), proj(c_, zs[r_ + 1])], fill=col + (255,))
    fl = fl.resize((W, H - horizon), Image.LANCZOS)
    a = np.asarray(fl).astype("float32"); fade = np.clip(np.linspace(0, 1, fl.height) * 2.5, 0, 1)[:, None, None]
    a[..., :3] = a[..., :3] * (.55 + .45 * fade)      # darker toward the horizon (depth)
    put(L, Image.fromarray(a.astype("uint8"), "RGBA"), W / 2, horizon + (H - horizon) / 2 + 400 * (1 - k), 1, _pin_(k * 1.5))

def spotlight(L, k, x=W / 2, top_w=120, bot_w=900, y_floor=1300, dark=.78):
    """Darken the frame except a soft cone of light from the top (the chess-stage look). Returns L."""
    if k <= 0: return L
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    d.polygon([(x - top_w / 2, -10), (x + top_w / 2, -10), (x + bot_w / 2, y_floor), (x - bot_w / 2, y_floor)], fill=255)
    d.ellipse((x - bot_w / 2, y_floor - 120, x + bot_w / 2, y_floor + 120), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(60))
    a = np.asarray(L).astype("float32"); mm = np.asarray(m).astype("float32")[..., None] / 255
    f = 1 - dark * k * (1 - mm); a[..., :3] *= f
    return Image.fromarray(np.clip(a, 0, 255).astype("uint8"), "RGBA")

# =====================================================================================
# Sprite treatments
# =====================================================================================
def glow(spr, col=PURPLE, r=26, strength=.9):
    """Soft coloured rim glow behind a sprite (the purple halo on objects in the references)."""
    P = r * 3; out = Image.new("RGBA", (spr.width + 2 * P, spr.height + 2 * P), (0, 0, 0, 0))
    m = Image.new("L", out.size, 0); m.paste(spr.getchannel("A"), (P, P))
    m = m.filter(ImageFilter.GaussianBlur(r)).point(lambda v: min(255, int(v * strength * 1.6)))
    out.paste(Image.new("RGBA", out.size, col + (255,)), (0, 0), m); out.alpha_composite(spr, (P, P)); return out

def persp(spr, lean=.35, side=0.0):
    """Tilt a flat sprite into a plane leaning back (lean) and turned sideways (side, -1..1)."""
    w, h = spr.size; dx = w * lean * .5; sy = h * side * .18
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    dst = [(dx, sy), (w - dx, -sy), (w, h + sy), (0, h - sy)]
    A = []; B_ = []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B_.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B_.append(v)
    coef = np.linalg.solve(np.array(A, float), np.array(B_, float))
    return spr.transform((w, int(h + abs(sy) * 2)), Image.PERSPECTIVE, tuple(coef), Image.BICUBIC)

# =====================================================================================
# Type moves
# =====================================================================================
def duo(L, lead, key, cx, cy, t, t_lead, t_key, gap=10, lead_col_k=1.0, key_from=1.35):
    """Small lead line above a BIG keyword ('I had to wait for' / 'HOURS').
    lead: sprite (small, light); key: sprite (big, bold, PURPLE or INK).
    Lead rises with a soft blur at t_lead; key lands at t_key: scale key_from -> 1 (back.out 1.6), blur 10 -> 0."""
    kl = tw(t, t_lead, .45, "power3.out")
    ky = cy + lead.height / 2 + gap + key.height / 2
    if kl > 0: put_fx(L, lead, cx, cy + 14 * (1 - kl), 1, None, kl * lead_col_k, 0, 6 * (1 - kl))
    kk = tw(t, t_key, .55, "back.out(1.6)")
    if kk > 0: put_fx(L, key, cx, ky, lerp(key_from, 1, kk), None, _pin_(kk * 2.2), 0, 10 * (1 - _pin_(kk * 1.4)))
    return ky + key.height / 2

def karaoke(L, words, times, cx, cy, t, gap=14, rtl=False, ghost=.22, t_show=None, maxw=940, line_h=None):
    """Words sit ghosted (22% alpha, slight blur) from t_show, then each fills to full as it is spoken.
    words: list of sprites (TW/TU/T); times: when each word is said (word_times(id)). rtl=True lays them right to
    left (Urdu). Lines wrap at maxw; cy is the centre of the whole block."""
    t_show = times[0] - .35 if t_show is None else t_show
    k0 = tw(t, t_show, .35)
    if k0 <= 0: return
    lines, cur, cw = [], [], 0
    for i, w in enumerate(words):
        if cur and cw + gap + w.width > maxw: lines.append(cur); cur, cw = [], 0
        cur.append(i); cw += (gap if len(cur) > 1 else 0) + w.width
    lines.append(cur)
    lh = line_h or max(w.height for w in words) * .95
    y = cy - lh * (len(lines) - 1) / 2
    for ln in lines:
        tot = sum(words[i].width for i in ln) + gap * (len(ln) - 1)
        x = cx + tot / 2 if rtl else cx - tot / 2
        for i in ln:
            w, tt = words[i], times[min(i, len(times) - 1)]
            kf = tw(t, tt - .04, .22, "power2.out")
            px = x - w.width / 2 if rtl else x + w.width / 2
            put_fx(L, w, px, y - 6 * kf, 1, None, k0 * lerp(ghost, 1, kf), 0, 3 * (1 - kf))
            x = x - w.width - gap if rtl else x + w.width + gap
        y += lh

def bar_word(L, spr, cx, cy, t, t0, col=PURPLE, pad=(30, 12), rtl=False, out_t=None):
    """A solid bar wipes in (expo.out .35s, 4% overshoot), then the word pops in white inside it.
    out_t: optional time the bar retracts (the 'PERFECTION' bar in the reference)."""
    bw, bh = spr.width + pad[0] * 2, spr.height + pad[1] * 2
    kb = tw(t, t0, .35, "expo.out")
    if out_t is not None: kb *= 1 - tw(t, out_t, .3, "power3.in")
    if kb <= 0: return
    w = bw * min(1.04, kb * 1.04) if kb < 1 else bw
    bar = rounded(max(4, w), bh, 6, col + (255,))
    x0 = cx + bw / 2 - w if rtl else cx - bw / 2
    put(L, bar, x0 + w / 2, cy)
    kt = tw(t, t0 + .18, .3, "back.out(2)")
    if out_t is not None: kt *= 1 - tw(t, out_t - .1, .2)
    if kt > 0: put_fx(L, spr, cx, cy + 6 * (1 - kt), lerp(.8, 1, kt), None, kt)

def icon_word(L, letters, slot, icon, font, col, cx, cy, t, t0, step=.06, spin=True):
    """A word whose letter at index `slot` is replaced by an icon (the clock in 'H⏰URS').
    Letters pop left to right (back.out), the icon spins in last. English/Latin text only."""
    sprs = [TW(c, font, col) if i != slot else None for i, c in enumerate(letters)]
    adv = [font.getlength(c) for c in letters]
    tot = sum(adv); x = cx - tot / 2
    for i, (s, a) in enumerate(zip(sprs, adv)):
        kk = tw(t, t0 + i * step, .4, "back.out(1.8)")
        if kk > 0:
            if s is not None: put_fx(L, s, x + a / 2, cy + 22 * (1 - kk), kk, None, _pin_(kk * 2))
            else:
                ki = tw(t, t0 + len(letters) * step, .55, "back.out(2)")
                if ki > 0: put(L, icon, x + a / 2, cy + font.size * .06, ki, 1, rot=(-120 * (1 - ki)) if spin else 0)
        x += a

def letter_build(L, word, font, col, cx, cy, t, t0, step=.07, from_right=True):
    """Letters appear one at a time, each with a small pop ('AN' -> 'CAN'); from_right builds right to left."""
    adv = [font.getlength(c) for c in word]; tot = sum(adv); x = cx - tot / 2
    order = range(len(word) - 1, -1, -1) if from_right else range(len(word))
    rank = {i: n for n, i in enumerate(order)}
    for i, (c, a) in enumerate(zip(word, adv)):
        kk = tw(t, t0 + rank[i] * step, .35, "back.out(2)")
        if kk > 0: put_fx(L, TW(c, font, col), x + a / 2, cy, lerp(.4, 1, kk), None, _pin_(kk * 2))
        x += a

def swell(L, left, key, right, cx, cy, t, t0, grow=2.2, gap=16, key_col_from=INK, key_col_to=PURPLE, font=None):
    """'im STILL learning': one word inside a line swells (scale 1 -> grow, ink -> purple) and its neighbours
    slide apart to make room. left/right: sprites; key: text with font given (re-rendered for crisp colour)."""
    k = tw(t, t0, .7, "back.out(1.5)")
    col = tuple(int(lerp(a, b, _pin_(k))) for a, b in zip(key_col_from, key_col_to))
    ks = TW(key, font, col); s = lerp(1, grow, k)
    kw_ = ks.width * s
    put(L, left, cx - kw_ / 2 - gap - left.width / 2, cy + (ks.height * s - left.height) * .28)
    put(L, ks, cx, cy, s)
    put(L, right, cx + kw_ / 2 + gap + right.width / 2, cy + (ks.height * s - right.height) * .28)

def ghost_word(L, text, t, k, cx=W / 2, cy=760, size=420, col=(190, 190, 210), alpha=.55, drift=18):
    """Giant pale serif word behind the hero (the 'EDITING' ghost letters). Slow horizontal drift."""
    if k <= 0: return
    s = TW(text, LO(size), col)
    put(L, s, cx - drift * t, cy, lerp(1.08, 1, k), alpha * k)

def ribbon(L, text, t, k=1.0, angle=-32, cy=1350, speed=140, col=PURPLE, fg=PAPER, size=46, band_h=110):
    """Diagonal band crossing the frame with repeating text scrolling along it ('WITH THE MONEY I EARNED')."""
    if k <= 0: return
    unit = TW(text + "   ·   ", ID("Bold", size), fg); n = int(2600 / unit.width) + 3
    strip = Image.new("RGBA", (unit.width * n, band_h), col + (255,))
    off = int((t * speed) % unit.width)
    for i in range(n): strip.alpha_composite(unit, (i * unit.width - off, (band_h - unit.height) // 2))
    strip = strip.crop((0, 0, 2400, band_h))
    w = int(2400 * k)
    if w < 4: return
    strip = strip.crop((0, 0, w, band_h)).rotate(angle, Image.BICUBIC, expand=True)
    put(L, with_shadow(strip, 14, (6, 10), .5), W / 2 - (2400 - w) * .35, cy)

def marker_loop(L, cx, cy, rx, ry, t, t0, col=(200, 40, 60), width=5):
    """Hand-drawn loop around a phrase (the red ellipse in the reference). Uses ir_doc.marker_circle."""
    marker_circle(L, cx, cy, rx, ry, tw(t, t0, .6, "power2.inOut"), col, width)

# =====================================================================================
# Graphic moves
# =====================================================================================
def arc_sweep(L, cx, cy, r, t, t0, dur=.9, a0=200, sweep=150, col=INK, width=5, trail=True):
    """Thin arc drawn around a hero object with a soft fading trail and a dot at the pen tip."""
    k = tw(t, t0, dur, "power2.inOut")
    if k <= 0: return
    S = 2; ov = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    bb = ((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S); end = a0 + sweep * k
    steps = 24 if trail else 1
    for i in range(steps):
        f0 = a0 + (end - a0) * i / steps; f1 = a0 + (end - a0) * (i + 1) / steps
        a = int(255 * ((i + 1) / steps) ** 1.5) if trail else 255
        d.arc(bb, f0, f1 + .5, fill=col + (a,), width=width * S)
    ex = cx + r * math.cos(math.radians(end)); ey = cy + r * math.sin(math.radians(end))
    d.ellipse(((ex - width * 1.4) * S, (ey - width * 1.4) * S, (ex + width * 1.4) * S, (ey + width * 1.4) * S), fill=col + (255,))
    L.alpha_composite(ov.resize((W, H), Image.LANCZOS))

def light_sweep(L, t, t0, dur=1.1, width=260, strength=.55, angle=35, col=(255, 255, 255)):
    """A diagonal band of light crossing the whole frame (the 'And FINALLY' sweep). Returns the new layer."""
    k = tw(t, t0, dur, "power2.inOut")
    if k <= 0 or k >= 1: return L
    ta = math.tan(math.radians(angle)); pos = lerp(-W * .6, W * 1.6, k)
    xx = _xx + _yy * ta * .35
    band = np.exp(-((xx - pos - _yy * .0) / width) ** 2) * strength
    a = np.asarray(L).astype("float32")
    a[..., :3] = a[..., :3] * (1 - band[..., None]) + np.array(col, "float32") * band[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype("uint8"), "RGBA")

def float_icons(L, t, icon, n=7, seed=3, area=(60, 280, W - 60, 1620), k=1.0, sizes=(.5, 1.2)):
    """Icons drifting slowly with a gentle spin and bob (the floating clocks / butterflies). Big ones are
    blurred a little for depth."""
    if k <= 0: return
    r = random.Random(seed)
    for i in range(n):
        x0, y0 = r.uniform(area[0], area[2]), r.uniform(area[1], area[3]); s = r.uniform(*sizes); ph = r.uniform(0, 6.28)
        x = x0 + 18 * math.sin(t * .5 + ph); y = y0 - 22 * t * (.3 + .4 * s) % 60 + 10 * math.sin(t * .8 + ph)
        ki = tw(t, .1 * i, .5, "back.out(1.6)") * k
        if ki > 0: put_fx(L, icon, x, y, s * ki, None, ki * (.55 + .4 * (s > .9)), math.sin(t * .6 + ph) * 18, 2.5 if s > 1.05 else 0)

def clock_icon(r=46, col=PURPLE, face=(240, 232, 255)):
    """Round alarm-clock icon (used for 'time' words). A symbol, not a brand."""
    S = 4; im = Image.new("RGBA", (int(r * 2.6 * S), int(r * 2.6 * S)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = im.width / 2
    for sx in (-1, 1): d.ellipse((c + sx * r * .75 * S - r * .32 * S, c - r * 1.05 * S - r * .32 * S, c + sx * r * .75 * S + r * .32 * S, c - r * 1.05 * S + r * .32 * S), fill=col + (255,))
    d.ellipse((c - r * S, c - r * S, c + r * S, c + r * S), fill=face + (255,), outline=col + (255,), width=int(r * .16 * S))
    d.line((c, c, c, c - r * .55 * S), fill=col + (255,), width=int(r * .12 * S)); d.line((c, c, c + r * .42 * S, c), fill=col + (255,), width=int(r * .12 * S))
    return im.resize((im.width // S, im.height // S), Image.LANCZOS)

def crescent_icon(r=40, col=GOLD):
    S = 4; im = Image.new("RGBA", (int(r * 2.4 * S), int(r * 2.4 * S)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = im.width / 2
    d.ellipse((c - r * S, c - r * S, c + r * S, c + r * S), fill=col + (255,))
    d.ellipse((c - r * .55 * S, c - r * 1.05 * S, c + r * 1.3 * S, c + r * .8 * S), fill=(0, 0, 0, 0))
    return im.resize((im.width // S, im.height // S), Image.LANCZOS)

# ---------- chess pieces (symbols for 'small becomes great', 'the first/most important') ----------
def _piece(kind, h, col, rim):
    S = 3; w = int(h * .62); im = Image.new("RGBA", (w * S, int(h * S)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx = w * S / 2; bw = w * S * .92
    d.rounded_rectangle((cx - bw / 2, h * S * .86, cx + bw / 2, h * S), int(h * S * .04), fill=col + (255,))
    d.rounded_rectangle((cx - bw * .4, h * S * .78, cx + bw * .4, h * S * .88), int(h * S * .03), fill=col + (255,))
    if kind == "pawn":
        d.polygon([(cx - bw * .16, h * S * .42), (cx + bw * .16, h * S * .42), (cx + bw * .3, h * S * .8), (cx - bw * .3, h * S * .8)], fill=col + (255,))
        d.ellipse((cx - bw * .27, h * S * .36, cx + bw * .27, h * S * .48), fill=col + (255,))
        d.ellipse((cx - bw * .24, h * S * .1, cx + bw * .24, h * S * .42), fill=col + (255,))
    else:
        d.polygon([(cx - bw * .14, h * S * .3), (cx + bw * .14, h * S * .3), (cx + bw * .3, h * S * .8), (cx - bw * .3, h * S * .8)], fill=col + (255,))
        d.ellipse((cx - bw * .3, h * S * .24, cx + bw * .3, h * S * .34), fill=col + (255,))
        d.polygon([(cx - bw * .26, h * S * .25), (cx + bw * .26, h * S * .25), (cx + bw * .18, h * S * .13), (cx - bw * .18, h * S * .13)], fill=col + (255,))
        for dx in (-.15, 0, .15):          # crown of three points (no cross: this is Islamic content)
            px_ = cx + bw * dx; top_ = h * S * (.02 if dx == 0 else .05)
            d.polygon([(px_ - bw * .07, h * S * .14), (px_ + bw * .07, h * S * .14), (px_, top_ + bw * .06)], fill=col + (255,))
            d.ellipse((px_ - bw * .045, top_, px_ + bw * .045, top_ + bw * .09), fill=col + (255,))
    a = np.asarray(im).astype("float32"); xs = np.linspace(-1, 1, im.width)[None, :]
    shade = (1 - .35 * np.clip(xs, 0, 1) + .25 * np.exp(-((xs + .35) / .12) ** 2))[..., None]   # specular stripe
    a[..., :3] = np.clip(a[..., :3] * shade + np.array(rim) * .0, 0, 255)
    return Image.fromarray(a.astype("uint8"), "RGBA").resize((w, int(h)), Image.LANCZOS)
def pawn(h=260, col=PURPLE): return _piece("pawn", h, col, (255, 255, 255))
def king(h=420, col=PURPLE): return _piece("king", h, col, (255, 255, 255))

def promote(L, x, base_y, t, t0, small=None, big=None):
    """A pawn glows, squashes, flashes and rises as a king (back.out), with a contact shadow.
    Symbol for 'the first and greatest', 'small deeds that grow'. No people."""
    small = small or pawn(); big = big or king()
    sh = disc(140, (20, 8, 40, 110)).resize((300, 40))
    put(L, sh, x, base_y + 4, 1, .8)
    if t < t0 + .25:
        g = tw(t, t0 - .35, .35)
        if g > 0: put_fx(L, disc(130, VIOLET_L + (255,)), x, base_y - small.height / 2, 1.2, None, .6 * g, 0, 30)
        sq = 1 - .12 * tw(t, t0, .25, "power2.in")
        put_fx(L, small, x, base_y, 1 / sq ** .5, sq, 1, 0, 0, 0, "bottom")
    else:
        k = tw(t, t0 + .25, .6, "back.out(1.7)")
        fl = 1 - tw(t, t0 + .25, .35)
        if fl > 0: put_fx(L, disc(170, (255, 255, 255, 255)), x, base_y - big.height * .5, 1.4, None, .8 * fl, 0, 40)
        put_fx(L, big, x, base_y, lerp(.7, 1, k), lerp(.4, 1, k), _pin_(k * 2), 0, 0, 0, "bottom")

# =====================================================================================
# Outro
# =====================================================================================
def dark_outro(prev, t, t0, brand="ISLAMIC REELS", line="Follow for more", share="Send it to someone who'd love this."):
    """The scene dims to 25% (power2.inOut .6s), a gold star pops, the brand rises, the Follow pill glints
    and a share line settles. prev: the last scene's RGBA frame at time t. Returns the composed frame."""
    k = tw(t, t0, .6, "power2.inOut")
    a = np.asarray(prev).astype("float32"); a[..., :3] *= 1 - .75 * k
    L = Image.fromarray(a.astype("uint8"), "RGBA")
    ks = tw(t, t0 + .3, .55, "back.out(1.8)")
    if ks > 0: put(L, star8(46, GOLD), W / 2, 760, ks, 1, rot=-40 * (1 - ks))
    kb = tw(t, t0 + .5, .6, "power4.out")
    if kb > 0: mask_rise(L, TW(brand, ID("Black", 96), PAPER), W / 2, 880, kb, 1.2, blur=8 * (1 - kb))
    kp = tw(t, t0 + .9, .7, "expo.out")
    if kp > 0:
        p = glint(pill(line, ID("Bold", 46), INK, PAPER), tw(t, t0 + 1.4, .9, "power2.inOut"))
        put(L, p, W / 2, 1030 + 60 * (1 - kp), press(t, t0 + 2.3, .93), _pin_(kp * 1.5))
        ripple(L, W / 2, 1030, tw(t, t0 + 2.35, .7, "power2.out"), 320, PAPER)
    kl = tw(t, t0 + 1.2, .6)
    if kl > 0: put(L, TW(share, LOI(40), (230, 222, 248)), W / 2, 1150 + 14 * (1 - kl), 1, kl)
    return L
