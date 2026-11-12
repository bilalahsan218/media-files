"""Islamic Reels: Ya'juj and Ma'juj, remake with an original look ("Forged").
Cinematic full-bleed night world drawn in code: parallax mountain ridges, a sky that changes mood with the story,
the wall between two mountains built from iron, heated, plated in molten copper, and levelled.
Type: Cinzel (inscription capitals) + Cormorant Garamond italic + Amiri + Noto Nastaliq. Accent: ember and copper.
Signature moves: text that is "forged" (a molten edge sweeps through the letters and they cool to bone), ember-burn
transitions, iris close, embers and dust, balance scale, falling blocks with physics.
No people are drawn; people are small dots. Sources: Al-Kahf 18:83-98, Al-Anbiya 21:96 (Sahih International);
Sahih al-Bukhari 7059, 3346; Sahih Muslim 2937."""
import math, functools, glob, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import ir_urdu as U
from ir_dark import *                 # engine helpers (put, put_fx, TW, T, text_mask, FA, ID, ON, WT, run, cli ...)
from ir_motion import _pin_
import ir_doc, ir_motion
def put(layer, spr, cx, cy, scale=1.0, alpha=1.0, rot=0):
    """put() that also works on RGB canvases (paste with mask = true blending)"""
    if alpha <= .004 or scale <= .01: return
    s = spr
    if rot: s = s.rotate(rot, Image.BICUBIC, expand=True)
    if abs(scale - 1) > 1e-3: s = s.resize((max(1, int(s.width * scale)), max(1, int(s.height * scale))), Image.BICUBIC)
    if alpha < .999: s = s.copy(); s.putalpha(s.getchannel("A").point(lambda v: int(v * alpha)))
    x, y = int(cx - s.width / 2), int(cy - s.height / 2)
    x0, y0 = max(0, -x), max(0, -y); x1, y1 = min(s.width, layer.width - x), min(s.height, layer.height - y)
    if x1 <= x0 or y1 <= y0: return
    c = s.crop((x0, y0, x1, y1))
    if layer.mode == "RGBA": layer.alpha_composite(c, (x + x0, y + y0))
    else: layer.paste(c, (x + x0, y + y0), c)
ir_doc.put = put; ir_motion.put = put
_tw = tw
def tw(lt, t0, d, ease="power3.out"): return 0.0 if lt <= t0 else _tw(lt, t0, d, ease)

U.load("timeline.json")
U.TL_BY_ID = {c["id"]: c for c in U.TL["chunks"]}
KEYS = set(open("keys.txt").read().split())

# ------------------------------------------------------------------ palette
# the user's dark-lime theme (house colours)
VOID = (11, 9, 10); INKD = (16, 18, 4)
BONE = (240, 238, 236); ASH = (130, 126, 128); DIM = (90, 88, 88)
EMBER = (206, 244, 30); HOT = (226, 255, 120); WHITEHOT = (246, 255, 214)        # LIME accent family
FIRE = (255, 118, 28); FHOT = (255, 206, 128)                                     # real fire stays fire-coloured
COPPER = (205, 116, 56); COPPER_L = (240, 170, 100); IRON = (50, 52, 54); STEEL = (130, 134, 128)
BLOOD = (240, 88, 68); MOON = (236, 240, 224); WATER = (110, 180, 210); LEAF = (150, 200, 60); POM = (200, 50, 66)
GOLDC = (206, 244, 30); COINC = (230, 190, 70)
INV = [False]          # the lime dua scene: dark ink on lime
U.DESK = VOID

def mixc(a, b, k): return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))

# ------------------------------------------------------------------ fonts
def _ff(pat): return glob.glob(os.path.expanduser(f"~/fonts/**/{pat}"), recursive=True)[0]
_FC = {}
def _font(key, pat, s):
    if (key, s) not in _FC: _FC[(key, s)] = ImageFont.truetype(_ff(pat), s)
    return _FC[(key, s)]
def CZ(s, w=700): return _font(f"cz{w}", f"cinzel-latin-{w}-normal.woff2", s)
def CG(s, w=500): return _font(f"cg{w}", f"cormorant-garamond-latin-{w}-italic.woff2", s)
def CGN(s, w=600): return _font(f"cgn{w}", f"cormorant-garamond-latin-{w}-normal.woff2", s)
def SL(s, w="SemiBold"): return ID(w, s)
FONTS = {"cz": CZ, "cz9": lambda s: CZ(s, 900), "cz4": lambda s: CZ(s, 400), "cg": CG, "cgn": CGN, "ar": FA, "sl": SL}

# ------------------------------------------------------------------ forged text (the signature move)
@functools.lru_cache(maxsize=600)
def forged(text, fk, size, col=BONE, track=0, gr=12, hot=EMBER):
    """Returns (cool RGBA uint8 array, letter mask float, glow mask float) on the same padded canvas."""
    ar = fk == "ar"; f = FONTS[fk](size)
    m = text_mask(text, f, track, ar)
    P = gr * 3; M = Image.new("L", (m.width + 2 * P, m.height + 2 * P), 0); M.paste(m, (P, P))
    G = M.filter(ImageFilter.GaussianBlur(gr))
    Ma = np.asarray(M).astype("float32") / 255; Ga = np.clip(np.asarray(G).astype("float32") / 255 * 2.2, 0, 1)
    cool = np.zeros(Ma.shape + (4,), "uint8"); cool[..., :3] = col; cool[..., 3] = (Ma * 255).astype("uint8")
    return Image.fromarray(cool, "RGBA"), Ma, Ga, np.array(col, "float32"), np.array(hot, "float32")

def forge(L, text, fk, size, x, y, t, t0, col=BONE, dur=None, until=None, track=0, gr=12, hot=EMBER, alpha=1.0, rise=0, ember_hold=0.0):
    """Molten edge sweeps through the text (LTR, or RTL for Arabic); letters cool to `col` behind it."""
    if t < t0: return 0
    cool, Ma, Ga, cc, hc = forged(text, fk, size, col, track, gr, hot)
    w = Ma.shape[1]; band = max(60, size * 1.6)
    dur = dur or min(1.1, .25 + w / 1400)
    q = (t - t0) / dur
    a = alpha
    if until is not None: a *= 1 - tw(t, until, .3)
    if a <= .004: return 0
    yo = rise * (1 - E("power3.out")(_pin_(q)))
    resid = ember_hold * (.55 + .45 * math.sin(t * 5.3))
    if q >= 1 + band / w + .05 and resid <= 0:
        put(L, cool, x, y + yo, 1, a); return 1
    xs = np.arange(w, dtype="float32")
    if fk == "ar": xs = w - xs
    front = -band + (w + 2 * band) * E("power2.inOut")(_pin_(q))
    rev = np.clip((front - xs) / 18, 0, 1)
    h = np.clip(1 - (front - xs) / band, 0, 1) * (xs < front + 18)
    h = np.maximum(h, resid)
    lc = cc[None, :] * (1 - h[:, None]) + hc[None, :] * h[:, None]
    lc = lc * (1 - h[:, None] * .0) + (np.array(WHITEHOT, "float32")[None, :] - lc) * (h[:, None] ** 3) * .7
    al = Ma * rev[None, :]; ag = Ga * h[None, :] * .85
    oa = al + ag * (1 - al); oa_s = np.maximum(oa, 1e-4)
    rgb = (lc[None, :, :] * al[..., None] + hc[None, None, :] * (ag * (1 - al))[..., None]) / oa_s[..., None]
    out = np.dstack([np.clip(rgb, 0, 255), np.clip(oa * 255 * a, 0, 255)]).astype("uint8")
    put(L, Image.fromarray(out, "RGBA"), x, y + yo); return 1

def fade_text(L, text, fk, size, x, y, t, t0, col=BONE, until=None, track=0, d=.5, rise=16, blur=6):
    k = tw(t, t0, d)
    if until is not None: k *= 1 - tw(t, until, .3)
    if k <= 0: return 0
    spr = forged(text, fk, size, col, track)[0]
    put_fx(L, spr, x, y + rise * (1 - k), 1, None, k, 0, blur * (1 - k)); return k

def gloss(L, text, x, y, t, t0, col=ASH, size=34, until=None):
    return fade_text(L, text, "cg", size, x, y, t, t0, col, until)

def label(L, text, x, y, t, t0, col=ASH, size=22, until=None, track=5):
    return fade_text(L, text, "sl", size, x, y, t, t0, col, until, track=track, rise=8, blur=3)

def rule(L, x, y, w, k, col=EMBER, a=1.0, thick=2):
    if k <= 0: return
    d = ImageDraw.Draw(L, "RGBA"); hw = w / 2 * k
    d.line((x - hw, y, x + hw, y), fill=col + (int(255 * a),), width=thick)
    d.polygon([(x - hw - 7, y), (x - hw, y - 4), (x - hw + 7 - 7, y + 4)], fill=col + (int(255 * a),))

def diamond(L, x, y, r, col, a=1.0):
    ImageDraw.Draw(L, "RGBA").polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], fill=col + (int(255 * a),))

def ar_word(L, ar, en, x, y, t, t0, col=HOT, size=92, until=None, en_col=BONE, en_size=34, hold=.0):
    """Arabic word forged right to left, ember rule, Cormorant gloss under it."""
    if t < t0: return 0
    forge(L, ar, "ar", size, x, y, t, t0, col, until=until, ember_hold=hold)
    rk = tw(t, t0 + .35, .6)
    if until is not None: rk *= 1 - tw(t, until, .3)
    rule(L, x, y + size * .78, 160, rk, EMBER, rk)
    if en: gloss(L, en, x, y + size * .78 + 44, t, t0 + .45, en_col, en_size, until)
    return 1

SAW_SPR = {}
def saw(text, size=40, col=BONE):
    """'THE MESSENGER OF ALLAH ﷺ' in Cinzel with the honorific in Amiri."""
    k = (text, size, col)
    if k not in SAW_SPR:
        a = forged(text, "cz", size, col, 2)[0]; b = forged("ﷺ", "ar", int(size * 1.25), GOLDC)[0]
        out = Image.new("RGBA", (a.width + b.width - 50, max(a.height, b.height)), (0, 0, 0, 0))
        out.alpha_composite(a, (0, (out.height - a.height) // 2)); out.alpha_composite(b, (a.width - 50, (out.height - b.height) // 2))
        SAW_SPR[k] = out
    return SAW_SPR[k]

# ------------------------------------------------------------------ frame furniture
ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII"]
@functools.lru_cache(maxsize=64)
def _hdr(n, title, src, inv=False):
    im = Image.new("RGBA", (W, 90), (0, 0, 0, 0))
    ac, bc, cc = (INKD, INKD, (60, 70, 10)) if inv else (EMBER, BONE, ASH)
    a = T(ROMAN[n], CZ(34, 700), ac); b = T(title, CZ(28, 600), bc, track=4)
    im.alpha_composite(a, (78, 45 - a.height // 2)); x = 78 + a.width + 18
    ImageDraw.Draw(im).line((x, 45, x + 34, 45), fill=ac + (200,), width=2); x += 52
    im.alpha_composite(b, (x, 45 - b.height // 2))
    if src:
        c = T(src, SL(21, "Medium"), cc, track=3); im.alpha_composite(c, (W - 78 - c.width, 45 - c.height // 2))
    return im
def chrome(L, n, title, src, t, t_scene):
    k = tw(t, t_scene + .15, .6)
    inv = INV[0]
    if k > 0: put(L, _hdr(n, title, src, inv), W / 2, 118 - 10 * (1 - k), 1, k)
    d = ImageDraw.Draw(L, "RGBA")
    p = min(1, t / R_END[0]); d.line((78, 1872, 78 + (W - 156) * p, 1872), fill=(INKD if inv else EMBER) + (230,), width=3)
    d.line((78 + (W - 156) * p, 1872, W - 78, 1872), fill=((90, 110, 10) if inv else (60, 58, 58)) + (200,), width=1)
    put(L, _brand(inv), W / 2, 1838, 1, .9)
@functools.lru_cache(maxsize=2)
def _brand(inv=False):
    a = T("ISLAMIC REELS", CZ(22, 700), INKD if inv else BONE, track=6); b = T("QURAN  ·  SUNNAH", SL(16, "Medium"), (60, 70, 10) if inv else ASH, track=4)
    im = Image.new("RGBA", (a.width + b.width + 60, max(a.height, b.height)), (0, 0, 0, 0))
    im.alpha_composite(a, (0, (im.height - a.height) // 2)); im.alpha_composite(b, (a.width + 60, (im.height - b.height) // 2))
    ImageDraw.Draw(im).polygon([(a.width + 30, im.height / 2 - 5), (a.width + 35, im.height / 2), (a.width + 30, im.height / 2 + 5), (a.width + 25, im.height / 2)], fill=(INKD if inv else EMBER) + (255,))
    return im
R_END = [300.0]

# ------------------------------------------------------------------ captions: words appear as spoken, bottom third
CAP_SIZE, CAP_MAXW, CAP_Y0, CAP_LH = 46, 900, 1590, 84
@functools.lru_cache(maxsize=4000)
def _cw(word, key, inv=False):
    if inv: return TU(word, CAP_SIZE, (70, 90, 0) if key else INKD, pad=10)
    return TU(word, CAP_SIZE, EMBER if key else BONE, pad=10)
@functools.lru_cache(maxsize=200)
def _cap_layout(cid, inv=False):
    words = U.TL_BY_ID[cid]["text"].split()
    sprs = [_cw(w, w.strip("،۔:؟,!") in KEYS, inv) for w in words]
    lines, cur, cw = [], [], 0
    for i, s in enumerate(sprs):
        ww = s.width - 12
        if cur and cw + ww > CAP_MAXW: lines.append(cur); cur, cw = [], 0
        cur.append(i); cw += ww
    lines.append(cur)
    pos = {}; n = len(lines)
    for li, ln in enumerate(lines):
        tot = sum(sprs[i].width - 12 for i in ln); x = W / 2 + tot / 2
        y = CAP_Y0 + (li - (n - 1) / 2) * CAP_LH
        for i in ln: pos[i] = (x - (sprs[i].width - 12) / 2, y); x -= sprs[i].width - 12
    return sprs, pos
CHUNK_IDS = [c["id"] for c in U.TL["chunks"]]
def captions(L, t):
    for n, cid in enumerate(CHUNK_IDS):
        s, e = ON(cid), OFF(cid)
        nxt = ON(CHUNK_IDS[n + 1]) if n + 1 < len(CHUNK_IDS) else e + 1.2
        hide = min(nxt - .02, e + .6)
        if not (s - .05 <= t < hide): continue
        sprs, pos = _cap_layout(cid, INV[0]); times = word_times(cid)
        ko = 1 - tw(t, hide - .18, .18, "power2.in")
        for i, spr in enumerate(sprs):
            k = tw(t, times[i] - .06, .28)
            if k <= 0: continue
            x, y = pos[i]
            put_fx(L, spr, x, y + 14 * (1 - k), 1, None, k * ko, 0, 5 * (1 - k))

# ------------------------------------------------------------------ screen-space helpers
_yy, _xx = np.mgrid[0:H, 0:W].astype("float32")
def _scrim():
    a = np.zeros((H, W), "float32")
    a += np.clip((_yy - 1330) / 330, 0, 1) ** 1.3 * .82          # bottom: captions sit on dark
    a += np.clip((300 - _yy) / 300, 0, 1) ** 1.5 * .7             # top: header
    im = np.zeros((H, W, 4), "uint8"); im[..., :3] = VOID; im[..., 3] = (np.clip(a, 0, 1) * 255).astype("uint8")
    return Image.fromarray(im, "RGBA")
SCRIM = _scrim()
def _half():
    dots = (((_xx % 6) < 2) & ((_yy % 6) < 2)).astype("float32")
    im = np.zeros((H, W, 4), "uint8"); im[..., :3] = 255; im[..., 3] = (dots * 7).astype("uint8")
    return Image.fromarray(im, "RGBA")
HALF = _half()

@functools.lru_cache(maxsize=32)
def radial(r, col, a=1.0, power=2.0):
    s = int(r * 2); yy, xx = np.mgrid[0:s, 0:s].astype("float32"); d = np.sqrt((xx - r) ** 2 + (yy - r) ** 2) / r
    al = np.clip(1 - d, 0, 1) ** power * a
    im = np.zeros((s, s, 4), "uint8"); im[..., :3] = col; im[..., 3] = (al * 255).astype("uint8"); return Image.fromarray(im, "RGBA")
def light(L, x, y, r, col, a):
    if a > .01: put(L, radial(int(r), col, 1.0), x, y, 1, min(1, a))

@functools.lru_cache(maxsize=8)
def dot_spr(r, col, g=0):
    s = disc(r, col + (255,))
    if g: s = glow(s, col, g, .7)
    return s

def zoom(img, z, cx=W / 2, cy=H / 2):
    if abs(z - 1) < .002: return img
    sw, sh = int(W * z), int(H * z); im = img.resize((sw, sh), Image.BICUBIC)
    x0 = int(cx * z - cx); y0 = int(cy * z - cy)
    x0 = max(0, min(sw - W, x0)); y0 = max(0, min(sh - H, y0))
    return im.crop((x0, y0, x0 + W, y0 + H))

def shake(t, t0, amp=14, d=.5):
    if not (t0 <= t < t0 + d): return 0, 0
    q = 1 - (t - t0) / d; return amp * q * math.sin(t * 91), amp * q * math.cos(t * 77)

# ------------------------------------------------------------------ transitions
def _noise(seed=4, sc=(5, 9)):
    rng = np.random.default_rng(seed); acc = np.zeros((H, W), "float32"); amp = 1.0; tot = 0
    for o in range(3):
        n = rng.random((sc[1] * 2 ** o + 2, sc[0] * 2 ** o + 2)).astype("float32")
        im = Image.fromarray((n * 255).astype("uint8")).resize((W, H), Image.BICUBIC)
        acc += np.asarray(im).astype("float32") / 255 * amp; tot += amp; amp *= .5
    acc /= tot; acc = (acc - acc.min()) / (acc.max() - acc.min())
    acc = .55 * acc + .45 * (1 - _yy / H); acc = (acc - acc.min()) / (acc.max() - acc.min()); return acc
NOISE = _noise()
def BURN(a, b, q):
    """Ember burn: the next scene eats through the last along a glowing edge."""
    q = E("power1.inOut")(_pin_(q)); th = -.08 + q * 1.16
    A = np.asarray(a.convert("RGB")).astype("float32"); B = np.asarray(b.convert("RGB")).astype("float32")
    m = np.clip((th - NOISE) / .03, 0, 1)[..., None]
    out = A * (1 - m) + B * m
    edge = np.clip(1 - np.abs(NOISE - th) / .025, 0, 1)[..., None]
    out = out + edge * np.array(EMBER, "float32") * 1.1 + (edge ** 4) * np.array(HOT, "float32") * .8
    return Image.fromarray(np.clip(out, 0, 255).astype("uint8")).convert("RGBA")
def XF(a, b, q): return Image.blend(a.convert("RGBA"), b.convert("RGBA"), E("power2.inOut")(_pin_(q)))
def DIP(a, b, q):
    q = _pin_(q); k = 1 - abs(q * 2 - 1); base = a if q < .5 else b
    return Image.blend(base.convert("RGBA"), Image.new("RGBA", (W, H), VOID + (255,)), E("power2.inOut")(k) * .92)
