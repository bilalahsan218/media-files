"""ir_urdu: the Urdu-narration layer for Islamic Reels (timeline cues, Nastaliq text, synced captions,
illustrated plate + camera, verified quote cards, word-by-word Urdu reveals, and the reel runner).

Every visual cue reads its time from timeline.json (written by narrate.py + align.py): the MEASURED start/end
of each narration chunk (exact to the sample) and word times inside chunks (snapped to energy dips).
  ON(id) = chunk start   OFF(id) = chunk end   WT(id, k) = start of word k   word_times(id) = all word starts
No people are drawn. Prophets are represented only by footprints, places and symbols.

Reel CLI (from run()):  python3 reel.py info | preview 2.8 37.5 ... | range 0 1800 part0.mp4
"""
import json, math, os, random, sys, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from ir_motion import *
from ir_motion import _pin_

TL, C = {"chunks": []}, {}
def load(path="timeline.json"):
    """Load the measured narration timeline (call once at the top of reel.py)."""
    global TL, C
    TL = json.load(open(path)); C = {c["id"]: c for c in TL["chunks"]}; return TL
def word_times(i): return [w["start"] for w in C[i]["words_aligned"]]
NUM = "۰۱۲۳۴۵۶۷۸۹"
def un(n):
    """Urdu digits. Noto Nastaliq has no Latin digits: always pass numbers through un() inside TU()."""
    return "".join(NUM[int(c)] if c.isdigit() else c for c in str(n))
def ON(i): return C[i]["start"]
def OFF(i): return C[i]["end"]
def WT(i, k): return C[i]["words_aligned"][k]["start"]

# ---------------------------------------------------------------- palette (house + illustration tints)
NIGHT = (30, 17, 60); DUSK = (74, 50, 130); MID = (98, 72, 160); SEA = (118, 96, 182); SEA2 = (150, 130, 206)
STONE = (205, 194, 234); STONE_D = (152, 136, 198); SAND = (240, 235, 250); WARM = (236, 206, 140)

# ---------------------------------------------------------------- Urdu Nastaliq text
_NQ = glob.glob(os.path.expanduser("~/fonts/**/noto-nastaliq-urdu-arabic-700-normal.woff2"), recursive=True)[0]
_NQC = {}
def NQ(s):
    if s not in _NQC: _NQC[s] = ImageFont.truetype(_NQ, s)
    return _NQC[s]
def TU(txt, size, col, pad=14):
    """Urdu display text in Noto Nastaliq. '!' and ':' (missing from the Nastaliq font) are set in Inter Bold;
    runs are laid right to left on one baseline. Use un() for digits and write '۔۔۔' instead of '…'."""
    import re
    if not re.search(r"[!:]", txt): return _TU(txt, size, col, pad)
    f, fp = NQ(size), ID("Bold", int(size * .62)); kw = dict(direction="rtl", language="ur")
    runs = []
    for seg in re.split(r"([!:])", txt):
        if seg in ("!", ":"): runs.append((seg, fp, {}))
        elif seg.strip(): runs.append((seg.strip(), f, kw))
    gap = f.getlength(" ", **kw)
    wid = sum(ft.getlength(r, **k) for r, ft, k in runs) + gap * len(runs)
    Hh = int(size * 2.6); im = Image.new("L", (int(wid) + 2 * pad, Hh), 0); d = ImageDraw.Draw(im); x = im.width - pad; base = int(size * 1.75)
    for j, (r, ft, k) in enumerate(runs):
        nxt = runs[j + 1][0] if j + 1 < len(runs) else ""
        d.text((x, base), r, font=ft, fill=255, anchor="rs", **k); x -= ft.getlength(r, **k) + (gap * .15 if nxt in ("!", ":") else gap)
    bb = im.getbbox(); im = im.crop((max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.width, bb[2] + pad), min(Hh, bb[3] + pad)))
    out = Image.new("RGBA", im.size, col + (255,)); out.putalpha(im); return out
def _TU(txt, size, col, pad=14):
    """Urdu sprite in Noto Nastaliq Urdu, RTL shaped by raqm (language ur)."""
    f = NQ(size); kw = dict(direction="rtl", language="ur"); bb = f.getbbox(txt, **kw)
    m = Image.new("L", (bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad), 0)
    ImageDraw.Draw(m).text((pad - bb[0], pad - bb[1]), txt, font=f, fill=255, **kw)
    im = Image.new("RGBA", m.size, col + (255,)); im.putalpha(m); return im
def soft_shadow(spr, r=6, a=.55, col=(10, 4, 25)):
    sh = Image.new("RGBA", (spr.width + 4 * r, spr.height + 4 * r), (0, 0, 0, 0))
    m = Image.new("L", sh.size, 0); m.paste(spr.getchannel("A").point(lambda v: int(v * a)), (2 * r, 2 * r + 3))
    sh.paste(Image.new("RGBA", sh.size, col + (255,)), (0, 0), m.filter(ImageFilter.GaussianBlur(r)))
    sh.alpha_composite(spr, (2 * r, 2 * r)); return sh

# ---------------------------------------------------------------- captions (chunk-synced, never early)
KEY = set()          # words drawn in gold in captions; set per reel: ir_urdu.KEY = {...}
SPK = {"M": "ماں", "C": "بچہ"}
CAP_W, CAP_F = 900, 50
def _wlen(w, f, kw):
    core = w.rstrip("!…:"); tail = w[len(core):]
    return f.getlength(core, **kw) + (ID("Bold", int(CAP_F * .8)).getlength(tail) if tail else 0)
def _caption(text, spk="N"):
    f = NQ(CAP_F); kw = dict(direction="rtl", language="ur"); sp = f.getlength(" ", **kw)
    words = text.split(); lines, cur, cw = [], [], 0
    for w in words:
        wl = _wlen(w, f, kw)
        if cur and cw + sp + wl > CAP_W - 80: lines.append(cur); cur, cw = [], 0
        cur.append((w, wl)); cw += (sp if len(cur) > 1 else 0) + wl
    lines.append(cur)
    LH = 92; bh = 44 + LH * len(lines)
    band = rounded(CAP_W, bh, 26, INK + (236,), GOLD + (255,) if spk == "C" else None, 3 if spk == "C" else 0)
    d = ImageDraw.Draw(band)
    for li, ln in enumerate(lines):
        tot = sum(wl for _, wl in ln) + sp * (len(ln) - 1); x = CAP_W / 2 + tot / 2; base = 22 + LH * li + 64
        for w, wl in ln:
            core = w.rstrip("!…:"); tail = w[len(core):]
            col = GOLD if core.strip("،۔؟,") in KEY else (255, 255, 255)
            d.text((x, base), core, font=f, fill=col + (255,), anchor="rs", **kw)
            if tail: d.text((x - f.getlength(core, **kw), base), tail, font=ID("Bold", int(CAP_F * .8)), fill=col + (255,), anchor="rs")
            x -= wl + sp
    out = soft_shadow(band, 10, .5)
    if spk in SPK:
        tag = pill(SPK[spk], NQ(30), INK if spk == "C" else PAPER, GOLD if spk == "C" else GREY, 26, 2, ar=True)
        full = Image.new("RGBA", (out.width, out.height + tag.height // 2 + 4), (0, 0, 0, 0))
        full.alpha_composite(out, (0, tag.height // 2 + 4)); full.alpha_composite(tag, (full.width - tag.width - 60, 0)); return full
    return out
CAPS = {}
CAP_Y = 1492
def captions(L, t):
    ids = [c["id"] for c in TL["chunks"]]
    for n, cid in enumerate(ids):
        s, e = ON(cid), OFF(cid)
        nxt = ON(ids[n + 1]) if n + 1 < len(ids) else e + 1.2
        hide = nxt if nxt - e < .8 else e + .45
        if s <= t < hide:
            if cid not in CAPS: CAPS[cid] = _caption(C[cid]["text"], C[cid].get("speaker", "N"))
            k = tw(t, s, .14, "power2.out"); ko = 1 - tw(t, hide - .14, .14, "power2.in") if hide != nxt else 1
            put(L, CAPS[cid], W / 2, CAP_Y + 10 * (1 - k), 1, k * ko)

# ---------------------------------------------------------------- the illustrated plate + camera
WW, WH, RS, SS = 880, 900, 1.25, 2
WSZ = (int(WW * RS), int(WH * RS))
PX, PY = 540, 868
PLATE = paper(940, 960, 401)
PLATE_SH = with_shadow(PLATE, 20, (12, 18), .65)
def Pt(pts, k=RS): return [(x * k, y * k) for x, y in pts]
def grad(top, bot, w=WSZ[0], h=WSZ[1], curve=1.0):
    y = (np.linspace(0, 1, h) ** curve)[:, None, None]
    a = np.array(top, "float32") * (1 - y) + np.array(bot, "float32") * y
    a = np.repeat(a, w, 1); al = np.full((h, w, 1), 255, "float32")
    return Image.fromarray(np.concatenate([a, al], 2).astype("uint8"), "RGBA")
def static(fn, w=WSZ[0], h=WSZ[1]):
    """Draw a static layer supersampled (fn(draw, k) uses world units * k), return at world res."""
    big = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0)); fn(ImageDraw.Draw(big), RS * SS)
    return big.resize((w, h), Image.LANCZOS)
def sprite(fn, w, h):
    """Small supersampled sprite of w x h world units (returned at world res)."""
    big = Image.new("RGBA", (int(w * RS * SS), int(h * RS * SS)), (0, 0, 0, 0)); fn(ImageDraw.Draw(big), RS * SS)
    return big.resize((int(w * RS), int(h * RS)), Image.LANCZOS)
def wput(world, spr, x, y, a=1.0, rot=0, sc=1.0):
    put(world, spr, x * RS, y * RS, sc, a, rot)
def wtext(world, spr, x, y, a=1.0):
    put(world, spr, x * RS, y * RS, RS, a)
def view(world, cx, cy, z, t=0, shake=1.0):
    cx += 2.2 * shake * math.sin(t * 1.3); cy += 1.6 * shake * math.sin(t * 1.7 + 1)
    w, h = WSZ[0] / z, WSZ[1] / z
    x0 = min(max(cx * RS - w / 2, 0), WSZ[0] - w); y0 = min(max(cy * RS - h / 2, 0), WSZ[1] - h)
    return world.resize((WW, WH), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))
def plate(L, win, y_off=0, a=1.0, tapes=True):
    pg = PLATE.copy(); pg.paste(win.convert("RGB"), (30, 30))
    ImageDraw.Draw(pg).rectangle((30, 30, 30 + WW - 1, 30 + WH - 1), outline=INK + (255,), width=3)
    full = PLATE_SH.copy(); full.alpha_composite(pg, (60, 60))
    put(L, full, PX, PY + y_off, 1, a)
    if tapes and a > .3:
        put(L, tape(170, 46, 41).rotate(-24, expand=True), PX - 440, PY - 470 + y_off, 1, a)
        put(L, tape(170, 46, 42).rotate(22, expand=True), PX + 440, PY - 470 + y_off, 1, a)
def eyebrow(L, text, t, t0, y=318):
    k = tw(t, t0, .7, "expo.out")
    if k > 0: mask_rise(L, hcat([star8(12, GOLD), TW(text, MONO(27), GREY)], 14), W / 2, y, k, 1.3)

def wave_lines(world, t, y0, amp, n, col, spacing=28, speed=1.0, width=3, x0=0, x1=None, freq=.018, seed=0):
    d = ImageDraw.Draw(world); x1 = x1 or WW
    for i in range(n):
        yy = y0 + i * spacing; ph = seed + i * 1.7; a = amp * (1 + .25 * i)
        pts = [(x, yy + a * math.sin(x * freq + t * speed * (1 + .15 * i) + ph) + a * .4 * math.sin(x * freq * 2.3 - t * speed * .7 + ph))
               for x in range(int(x0), int(x1) + 12, 12)]
        d.line(Pt(pts), fill=col, width=int(width * RS))

def footprints(world, path, k, col=INK, side=9, step=26, size=(9, 14), alpha=255, offset=0):
    """Two trails of footprints along a path (two travellers), revealed up to fraction k."""
    if k <= 0: return
    seg = [math.dist(path[i], path[i + 1]) for i in range(len(path) - 1)]; tot = sum(seg)
    d = ImageDraw.Draw(world); s = 10.0; n = 0
    while s < tot * k:
        acc, i = 0, 0
        while i < len(seg) - 1 and acc + seg[i] < s: acc += seg[i]; i += 1
        f = (s - acc) / seg[i]; ax, ay = path[i]; bx, by = path[i + 1]
        x, y = ax + (bx - ax) * f, ay + (by - ay) * f; ang = math.atan2(by - ay, bx - ax)
        nx, ny = -math.sin(ang), math.cos(ang)
        for trail, sh in ((0, -1), (1, 1)):
            lr = 1 if (n + trail) % 2 else -1
            px = x + nx * (sh * 22 + lr * side) + offset; py = y + ny * (sh * 22 + lr * side)
            fade = min(1, (tot * k - s) / 60 + .35)
            w_, h_ = size
            d.ellipse(Pt([(px - w_ / 2, py - h_ / 2), (px + w_ / 2, py + h_ / 2)]), fill=col + (int(alpha * fade),))
        s += step; n += 1

# ---------------------------------------------------------------- quote cards (verified text only)
class QCard:
    def __init__(self, label, lines, ref, seed, w=860, size=40, hl=None):
        self.f = LOI(size); self.lh = int(size * 1.36); self.lines = lines; self.hl = hl or []
        self.lab = TW(label, MONO(23), GREY); self.ref = TW(ref, MONO(23), GOLD)
        self.spr = [TW(l, self.f, INK) for l in lines]
        self.w = w; self.h = 64 + self.lh * len(lines) + 64; self.base = paper(w, self.h, seed)
    def frame(self, t, t_in, t_hl=None, t_circ=None):
        pg = self.base.copy(); onto(pg, self.lab, 44, 22, tw(t, t_in + .15, .35), 8)
        if t_hl is not None:
            for li, a, b in self.hl:
                x0 = 44 + 8 + self.f.getlength(self.lines[li][:self.lines[li].index(a)])
                x1 = 44 + 8 + self.f.getlength(self.lines[li][:self.lines[li].index(b, self.lines[li].index(a)) + len(b)])
                highlight(pg, x0, 64 + self.lh * li + self.lh * .55, x1 - x0, self.lh * .78, tw(t, t_hl, .5, "power2.inOut"))
        per = .42
        for i, s in enumerate(self.spr): typed_on(pg, s, 44, 56 + self.lh * i, (t - t_in - .25 - i * per) / per)
        onto(pg, self.ref, self.w - 44 - self.ref.width, self.h - 52, tw(t, t_in + .3 + per * len(self.spr), .4), 6)
        if t_circ is not None and self.hl:
            li, a, b = self.hl[0]
            x0 = 44 + self.f.getlength(self.lines[li][:self.lines[li].index(a)]); x1 = 44 + self.f.getlength(self.lines[li][:self.lines[li].index(b, self.lines[li].index(a)) + len(b)])
            marker_circle(pg, (x0 + x1) / 2 + 10, 64 + self.lh * li + self.lh * .5, (x1 - x0) / 2 + 18, self.lh * .62, tw(t, t_circ, .55), width=5)
        return pg
    def draw(self, L, t, t_in, y, rot=-1.0, **kw):
        k = tw(t, t_in, .65, "power4.out")
        if k <= 0: return
        pg = page_out(self.frame(t, t_in, **kw), rot, 14)
        put(L, pg, W / 2, y + 260 * (1 - k), 1, _pin_(k * 1.6))
        put(L, tape(150, 42, 7).rotate(-8, expand=True), W / 2 - self.w / 2 + 60, y - self.h / 2 + 260 * (1 - k), 1, _pin_(k * 1.6))


# ---------------------------------------------------------------- word-by-word Urdu reveal
WCACHE = {}; CUR_T = [0.0]
def kinetic_words(L, text, size, col, cx, cy, times, gold=(), t=None):
    """Urdu line revealed right to left, word i rising and un-blurring at times[i] (use word_times(id))."""
    t = CUR_T[0] if t is None else t
    f = NQ(size); kw = dict(direction="rtl", language="ur"); ws = text.split(); sp = f.getlength(" ", **kw)
    wl = [_wlen(w, f, kw) for w in ws]; tot = sum(wl) + sp * (len(ws) - 1); x = cx + tot / 2
    for i, (w, l) in enumerate(zip(ws, wl)):
        kk = tw(t, times[min(i, len(times) - 1)], .45, "power3.out")
        if kk > 0:
            key = (w, size, col, w in gold)
            if key not in WCACHE: WCACHE[key] = TU(w, size, GOLD if w in gold else col)
            put_fx(L, WCACHE[key], x - l / 2, cy + 18 * (1 - kk), 1, None, kk, 0, 10 * (1 - kk))
        x -= l + sp
def urdu_words(text, size, col, gold=()):
    """Sprites for each Urdu word (for ir_viral.karaoke(..., rtl=True))."""
    return [TU(w, size, GOLD if w in gold else col) for w in text.split()]

# ---------------------------------------------------------------- the reel runner
def run(scenes, first_ids, trans, end_fn, tail=3.2, end_len=3.7, win=(.25, .35), push=.02, caps=True, outro=None):
    """Assemble scenes on the narration clock and expose the CLI.
    scenes: list of f(t) -> RGBA (t = GLOBAL time, so cues can use ON/WT directly).
    first_ids: chunk id that opens each scene after the first (len(scenes) - 1 items).
    trans: transitions, len(scenes) (the last one leads into the end card).
    end_fn: end card f(local_t); or pass outro=ir_viral.dark_outro to dim the last scene instead.
    Scene boundaries sit in the pause before each opening chunk, so a cut never lands on a word."""
    ids = [c["id"] for c in TL["chunks"]]
    def boundary(cid):
        prev_end = OFF(ids[ids.index(cid) - 1]); return max(prev_end - .02, ON(cid) - .72) + .25
    B = [0.0] + [boundary(c) for c in first_ids]
    END_T = OFF(ids[-1]) + tail; B.append(END_T); DUR = round(END_T + end_len, 2)
    allsc = list(scenes) + [None]
    def scene_at(i, t):
        if i == len(allsc) - 1:
            if outro is not None: return outro(allsc[i - 1](t), t, END_T)
            return end_fn(t - B[i] + .25)
        return allsc[i](t)
    def frame(t):
        CUR_T[0] = t
        i = max(j for j in range(len(B)) if B[j] <= t); img = None
        for j in range(1, len(B)):
            if outro is not None and j == len(B) - 1: continue
            if B[j] - win[0] <= t < B[j] + win[1]:
                q = (t - (B[j] - win[0])) / sum(win); img = trans[j - 1](scene_at(j - 1, t), scene_at(j, t), q); break
        if img is None: img = scene_at(i, t)
        z = 1 + push * c01((t - B[i]) / 8)
        if z > 1.001:
            sw, sh = int(W * z), int(H * z); img = img.resize((sw, sh), Image.BICUBIC).crop(((sw - W) // 2, (sh - H) // 2, (sw - W) // 2 + W, (sh - H) // 2 + H))
        if caps and t < END_T - .1: captions(img, t)
        arr = np.asarray(img.convert("RGB")).astype("float32") * VIG[..., None] + GRAIN[int(round(t * FPS)) % 6]
        if t < .3: arr = arr * eo(t / .3) + np.array(DESK) * (1 - eo(t / .3))
        if t > DUR - .6: arr = arr * eo((DUR - t) / .6) + np.array(DESK) * (1 - eo((DUR - t) / .6))
        return np.clip(arr, 0, 255).astype("uint8")
    def render_range(a, b, out):
        import subprocess
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                               "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for n in range(a, b):
            ff.stdin.write(frame(n / FPS).tobytes())
            if n % 150 == 0: print(out, n, flush=True)
        ff.stdin.close(); ff.wait()
    return dict(B=B, DUR=DUR, END_T=END_T, frame=frame, render_range=render_range)

def cli(R):
    """Command line for reel.py:  python3 reel.py info | preview 2.8 9.5 ... | range 0 1800 part0.mp4"""
    if len(sys.argv) < 2: print("usage: info | preview t1 t2 ... | range a b out.mp4"); return
    cmd = sys.argv[1]
    if cmd == "preview":
        os.makedirs("pv", exist_ok=True)
        for x in sys.argv[2:]: Image.fromarray(R["frame"](float(x))).save(f"pv/{float(x):07.2f}.png"); print("pv", x)
    elif cmd == "range": R["render_range"](int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    elif cmd == "info": print("DUR", R["DUR"], "frames", int(R["DUR"] * FPS)); print("B", [round(x, 2) for x in R["B"]])
