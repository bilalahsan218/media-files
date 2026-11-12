"""Dark-lime look for Islamic Reels (from the user's reference reel, Nov 2026).

Near-black halftone background with an olive glow, neon LIME accent (CORAL red for the negative), a thin
chapter header ("02 · THE GRAVE" left, "● STAGE  QABR" right), a headline at the top that builds word by
word as it is spoken (keywords in lime), dark rounded UI cards with thin borders, lime pills and tilted
stickers, a stage strip (film-strip progress), full-lime flash scenes for the aha, and a brand footer.
Build on ir_urdu (TU, word_times, ON/WT) and ir_viral.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import ir_urdu as U
from ir_urdu import *            # noqa
from ir_viral import *           # noqa
from ir_motion import _pin_

BG = (11, 9, 10)
LIME = (206, 244, 30)
LIME_D = (120, 140, 20)
CORAL = (240, 88, 68)
CARD = (24, 22, 24)
EDGE = (58, 56, 58)
MUTE = (130, 126, 128)
WHITE = (240, 238, 236)
U.DESK = BG                       # run() fades in/out from this colour

def IDF(w, s): return ID(w, s)
def SANS(s, w="Bold"): return ID(w, s)

# ------------------------------------------------------------------ background
_yy, _xx = np.mgrid[0:H, 0:W]
def _bg(glow_y=.42, glow=(64, 74, 10)):
    g = np.exp(-(((_xx - W / 2) / (W * .7)) ** 2 + ((_yy - H * glow_y) / (H * .16)) ** 2))
    a = np.array(BG, "float32") + np.array(glow, "float32") * g[..., None] * .9
    dots = (((_xx % 6) < 2) & ((_yy % 6) < 2)).astype("float32")[..., None]       # halftone dot grid
    a = a + dots * 7
    vg = np.clip(1 - .45 * (((_xx - W / 2) / (W * .8)) ** 2 + ((_yy - H / 2) / (H * .7)) ** 2), .55, 1)[..., None]
    return Image.fromarray(np.clip(a * vg, 0, 255).astype("uint8")).convert("RGBA")
BG_IMG = _bg()
def _lime_bg():
    g = np.exp(-(((_xx - W / 2) / (W * .8)) ** 2 + ((_yy - H * .5) / (H * .6)) ** 2))
    a = np.array((168, 205, 10), "float32") + (np.array(LIME, "float32") - np.array((168, 205, 10), "float32")) * g[..., None]
    dots = (((_xx % 6) < 2) & ((_yy % 6) < 2)).astype("float32")[..., None]
    return Image.fromarray(np.clip(a - dots * 6, 0, 255).astype("uint8")).convert("RGBA")
LIME_IMG = _lime_bg()
def dark(): return BG_IMG.copy()
def lime(): return LIME_IMG.copy()

# ------------------------------------------------------------------ frame furniture
def header(L, left, stage_lbl, stage_key, t, inv=False):
    fg = (20, 22, 6) if inv else WHITE; mu = (60, 70, 10) if inv else MUTE
    d = ImageDraw.Draw(L)
    put(L, TW(left, SANS(26, "SemiBold"), fg), 80 + TW(left, SANS(26, "SemiBold"), fg).width / 2, 106)
    r = TW(stage_key, SANS(26, "Bold"), (20, 22, 6) if inv else LIME); m = TW(stage_lbl, SANS(26, "Medium"), mu)
    x1 = W - 80; put(L, r, x1 - r.width / 2, 106); put(L, m, x1 - r.width - 10 - m.width / 2, 106)
    cx = x1 - r.width - m.width - 36; pulse = .5 + .5 * math.sin(t * 4)
    dot = disc(9, (20, 22, 6) if inv else LIME)
    if not inv: put(L, glow(dot, LIME, 10, .4 + .4 * pulse), cx, 106)
    else: put(L, dot, cx, 106)
    d.line((80, 140, W - 80, 140), fill=((40, 48, 6) if inv else (44, 42, 44)) + (255,), width=2)
def footer(L, inv=False):
    fg = (20, 22, 6) if inv else WHITE; mu = (60, 70, 10) if inv else MUTE
    d = ImageDraw.Draw(L); d.line((80, 1800, W - 80, 1800), fill=((40, 48, 6) if inv else (44, 42, 44)) + (255,), width=2)
    a = TW("ISLAMIC REELS", SANS(30, "Bold"), fg); b = TW("QURAN  ·  SUNNAH  ·  REMINDER", SANS(20, "SemiBold"), mu)
    put(L, a, 80 + a.width / 2, 1842); put(L, b, 80 + a.width + 22 + b.width / 2, 1844)

def headline(L, cid, t, size=72, keys=(), inv=False, y0=245, x_right=W - 80, maxw=920, line_h=None):
    """The chunk's Urdu words appear right to left as they are spoken (rise + unblur). keys: words in lime."""
    words = U.TL_BY_ID[cid]["text"].split() if hasattr(U, "TL_BY_ID") else None
    if words is None:
        U.TL_BY_ID = {c["id"]: c for c in U.TL["chunks"]}; words = U.TL_BY_ID[cid]["text"].split()
    times = word_times(cid); line_h = line_h or int(size * 1.62)
    fg = (16, 18, 4) if inv else WHITE; kc = (16, 18, 4) if inv else LIME
    sprs = [TU(w, size, kc if (w.strip("،۔:؟,") in keys) else fg) for w in words]
    x, y, rows = x_right, y0, []
    for s in sprs:
        if x - s.width < x_right - maxw: x, y = x_right, y + line_h
        rows.append((x - s.width / 2, y)); x -= s.width - 2
    for s, (cx, cy), wt in zip(sprs, rows, times):
        k = tw(t, wt - .05, .32, "power3.out")
        if k <= 0: continue
        if inv and words: pass
        put_fx(L, s, cx, cy + 22 * (1 - k), 1, None, k, 0, 8 * (1 - k))

# ------------------------------------------------------------------ components
def dcard(w, h, r=30, fill=CARD, edge=EDGE, ew=2, inv=False):
    S = 2; im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * S - 1, h * S - 1), r * S, fill=fill + (255,), outline=edge + (255,), width=ew * S)
    return im.resize((w, h), Image.LANCZOS)
def shadowed(spr, r=26, a=.65):
    pad = r * 2; im = Image.new("RGBA", (spr.width + pad * 2, spr.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", spr.size, (0, 0, 0, int(255 * a))); sh.putalpha(spr.getchannel("A").point(lambda v: int(v * a)))
    im.alpha_composite(sh, (pad, pad + 16)); im = im.filter(ImageFilter.GaussianBlur(r)); im.alpha_composite(spr, (pad, pad)); return im
def lpill(text, size=30, fg=(16, 18, 4), bg=LIME, padx=26, pady=12, font=None, ur=False):
    t_ = TU(text, size, fg) if ur else TW(text, font or SANS(size, "Bold"), fg)
    w, h = t_.width + padx * 2, t_.height + pady * 2
    p = rounded(w, h, h // 2 if h < 90 else 30, bg); p.alpha_composite(t_, (padx, pady)); return p
def lbar(num, text, w=760, size=34):
    """The reference's '01  DELAY' bar: lime bar with a black number chip."""
    h = 86; b = rounded(w, h, 18, LIME); chip = rounded(64, 52, 10, (16, 18, 4))
    n = TW(num, SANS(28, "Bold"), LIME); chip.alpha_composite(n, ((64 - n.width) // 2, (52 - n.height) // 2))
    b.alpha_composite(chip, (18, 17)); tt = TW(text, SANS(size, "Bold"), (16, 18, 4)); b.alpha_composite(tt, (100, (h - tt.height) // 2))
    d = ImageDraw.Draw(b); d.rounded_rectangle((w - 90, 36, w - 36, 50), 6, fill=(16, 18, 4, 255)); return b
def sticker(text, size=44, bg=LIME, fg=(16, 18, 4), ur=False):
    t_ = TU(text, size, fg) if ur else TW(text, SANS(size, "Black"), fg)
    w, h = t_.width + 50, t_.height + 26; im = Image.new("RGBA", (w + 12, h + 12), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, w + 5, h + 5), 10, fill=bg + (255,), outline=(16, 18, 4, 255), width=5)
    im.alpha_composite(t_, (31, 19)); return im
def check_icon(r=22, bg=LIME, fg=(16, 18, 4)):
    S = 3; im = Image.new("RGBA", (r * 2 * S, r * 2 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, r * 2 * S - 1, r * 2 * S - 1), fill=bg + (255,))
    d.line([(r * .55 * S, r * 1.05 * S), (r * .9 * S, r * 1.4 * S), (r * 1.5 * S, r * .7 * S)], fill=fg + (255,), width=int(r * .28 * S), joint="curve")
    return im.resize((r * 2, r * 2), Image.LANCZOS)
def lock_icon(s=40, col=LIME):
    S = 3; w = s * S; im = Image.new("RGBA", (w, int(w * 1.25)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.arc((w * .2, 0, w * .8, w * .6), 180, 360, fill=col + (255,), width=int(w * .12)); d.line((w * .26, w * .3, w * .26, w * .5), fill=col + (255,), width=int(w * .12))
    d.line((w * .74, w * .3, w * .74, w * .5), fill=col + (255,), width=int(w * .12))
    d.rounded_rectangle((0, w * .48, w - 1, w * 1.25 - 1), w * .12, fill=col + (255,)); d.ellipse((w * .42, w * .7, w * .58, w * .86), fill=(16, 18, 4, 255))
    return im.resize((s, int(s * 1.25)), Image.LANCZOS)
def hourglass(k_sand, h=300, col=LIME, frame=WHITE):
    """Hourglass: k_sand 0 = all sand on top, 1 = all at the bottom."""
    S = 2; w = int(h * .62); im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    W_, H_ = w * S, h * S; m = H_ / 2; top = int(H_ * .1); bot = int(H_ * .9)
    d.rounded_rectangle((0, 0, W_, top), 10 * S, fill=frame + (255,)); d.rounded_rectangle((0, bot, W_, H_), 10 * S, fill=frame + (255,))
    g = W_ * .1
    up = [(g, top), (W_ - g, top), (W_ / 2 + 10 * S, m), (W_ / 2 - 10 * S, m)]; dn = [(W_ / 2 - 10 * S, m), (W_ / 2 + 10 * S, m), (W_ - g, bot), (g, bot)]
    d.polygon(up, outline=frame + (255,), width=6 * S); d.polygon(dn, outline=frame + (255,), width=6 * S)
    k = _pin_(k_sand)
    yt = top + (m - top) * k                       # top sand surface drops
    wt = lambda y: (W_ / 2 - g) * (m - y) / (m - top) + 10 * S
    if k < 1: d.polygon([(W_ / 2 - wt(yt), yt), (W_ / 2 + wt(yt), yt), (W_ / 2 + 10 * S, m - 4), (W_ / 2 - 10 * S, m - 4)], fill=col + (255,))
    hb = (bot - m) * k * .9; yb = bot - hb
    wb = lambda y: (W_ / 2 - g) * (y - m) / (bot - m) + 10 * S
    if k > 0:
        d.polygon([(W_ / 2 - wb(yb), yb), (W_ / 2 + wb(yb), yb), (W_ / 2 + wb(bot - 6), bot - 6), (W_ / 2 - wb(bot - 6), bot - 6)], fill=col + (255,))
        if k < 1: d.line((W_ / 2, m, W_ / 2, bot - 8), fill=col + (255,), width=4 * S)
    return im.resize((w, h), Image.LANCZOS)

STAGES = [("موت", "DEATH"), ("قبر", "GRAVE"), ("صور", "HORN"), ("حساب", "RECKONING"), ("انجام", "END")]
def strip(L, active, t, k=1.0, y=1530, inv=False, done_upto=None):
    """Stage strip (the reference's HOOK·DELAY·REHOOK·PAYOFF film strip), right to left for Urdu.
    active: index 0..4 lit lime; earlier ones get a check, later ones a lock."""
    if k <= 0: return
    n = 5; tw_, gap = 172, 12; x0 = W / 2 + (n * tw_ + (n - 1) * gap) / 2 - tw_ / 2
    base = dcard(n * tw_ + (n - 1) * gap + 40, 150, 26, (18, 16, 18) if not inv else (16, 18, 4), (48, 46, 48) if not inv else (16, 18, 4))
    put(L, base, W / 2, y + 30 * (1 - k), 1, k)
    done_upto = active if done_upto is None else done_upto
    for i, (ur, en) in enumerate(STAGES):
        x = x0 - i * (tw_ + gap); on = i == active
        kk = tw(t, -1, .01) if True else 1
        tile = dcard(tw_, 108, 18, LIME if on else (30, 28, 30), LIME if on else (60, 58, 60))
        lab = TU(ur, 40, (16, 18, 4) if on else (WHITE if i < done_upto else MUTE))
        tile.alpha_composite(lab, ((tw_ - lab.width) // 2, 2))
        e = TW(en, SANS(16, "Bold"), (16, 18, 4) if on else MUTE); tile.alpha_composite(e, ((tw_ - e.width) // 2, 78))
        put(L, tile, x, y + 30 * (1 - k), 1.06 if on else 1, k)
        if i < done_upto: put(L, check_icon(15), x + tw_ / 2 - 14, y - 46 + 30 * (1 - k), 1, k)
        elif i > active: put(L, lock_icon(20, MUTE), x + tw_ / 2 - 16, y - 46 + 30 * (1 - k), 1, k)
