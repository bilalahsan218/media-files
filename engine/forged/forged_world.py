# ==================================================================== the world (all drawn in code)
MOODS = {   # top, mid, horizon, horizon glow colour, glow strength, stars  (dark-lime theme)
    "night":  ((9, 8, 9), (14, 14, 12), (32, 36, 18), (64, 74, 10), .55, 1.0),
    "blood":  ((11, 8, 8), (26, 12, 11), (70, 28, 22), (150, 52, 40), .55, .55),
    "forge":  ((10, 8, 8), (20, 14, 10), (50, 30, 14), (130, 62, 20), .45, .5),
    "dusk":   ((10, 9, 10), (24, 26, 14), (90, 104, 24), (170, 206, 26), .8, .3),
    "dawn":   ((10, 10, 10), (30, 34, 16), (120, 144, 28), (206, 244, 30), .75, .2),
    "storm":  ((10, 10, 10), (20, 20, 20), (42, 44, 40), (66, 72, 50), .25, 0.0),
    "morning": ((22, 26, 12), (60, 74, 20), (150, 186, 40), (206, 244, 30), .7, 0.0),
    "gold":   ((150, 186, 8), (180, 218, 20), (206, 244, 30), (232, 255, 130), .6, 0.0),
    "dead":   ((9, 9, 9), (18, 18, 17), (38, 38, 34), (56, 58, 46), .25, .3),
}
HZ = 1000          # horizon line of the sky gradient
@functools.lru_cache(maxsize=16)
def _sky(mood, glow_x=540):
    top, mid, hor, gc, gs, _ = MOODS[mood]
    y = _yy[:, :1]
    k1 = np.clip(y / 620, 0, 1); k2 = np.clip((y - 620) / (HZ - 620), 0, 1)
    c = np.where(y < 620, np.array(top) + (np.array(mid) - np.array(top)) * k1, np.array(mid) + (np.array(hor) - np.array(mid)) * k2)
    c = np.broadcast_to(c[:, None, :], (H, W, 3)).astype("float32").copy()
    g = np.exp(-(((_xx - glow_x) / 620) ** 2 + ((_yy - HZ) / 260) ** 2))[..., None] * gs
    c = c + (np.array(gc, "float32") - c) * g * .8
    return np.clip(c, 0, 255)
def sky(mood, mood2=None, k=0.0, glow_x=540):
    a = _sky(mood, glow_x)
    if mood2 and k > 0: a = a + (_sky(mood2, glow_x) - a) * k
    return Image.fromarray(a.astype("uint8"))
def stars_of(mood, mood2=None, k=0.0):
    s = MOODS[mood][5]
    return s + (MOODS[mood2][5] - s) * k if mood2 else s

_SR = np.random.default_rng(11)
STARS = [(_SR.uniform(0, W), _SR.uniform(0, 1050) ** 1.0 * _SR.uniform(.3, 1), _SR.uniform(.6, 2.2), _SR.uniform(0, 6.28), _SR.uniform(.5, 2.5)) for _ in range(260)]
def stars(L, t, a=1.0, ymax=1100):
    if a <= .02: return
    d = ImageDraw.Draw(L, "RGBA")
    for x, y, r, ph, sp in STARS:
        if y > ymax: continue
        tw_ = .55 + .45 * math.sin(t * sp + ph); al = int(255 * a * tw_ * (1 - y / 1300))
        if al < 8: continue
        d.ellipse((x - r / 2, y - r / 2, x + r / 2, y + r / 2), fill=(230, 236, 255, al))
@functools.lru_cache(maxsize=4)
def _moon(r=58, phase=.62):
    s = int(r * 2 + 8); m = Image.new("L", (s * 3, s * 3), 0); d = ImageDraw.Draw(m)
    o = s * 3 / 2; R_ = r * 3
    d.ellipse((o - R_, o - R_, o + R_, o + R_), fill=255)
    off = R_ * 2 * (1 - phase) * .9
    d.ellipse((o - R_ + off * .9 + R_ * .5, o - R_ - R_ * .1, o + R_ + off * .9 + R_ * .5, o + R_ - R_ * .1), fill=0)
    m = m.resize((s, s), Image.LANCZOS)
    im = Image.new("RGBA", (s, s), MOON + (255,)); im.putalpha(m)
    return glow(im, (160, 180, 230), 30, .5)
def moon(L, x, y, a=1.0): put(L, _moon(), x, y, 1, a)

# ---------- ridges (parallax layers) ----------
def _ridge(n, base, amp, rough, seed):
    rng = np.random.default_rng(seed); pts = np.zeros(n + 1, "float32"); step = n; scale = amp
    pts[0] = rng.uniform(-1, 1) * amp; pts[n] = rng.uniform(-1, 1) * amp
    while step > 1:
        h = step // 2
        for i in range(h, n, step): pts[i] = (pts[i - h] + pts[i + h]) / 2 + rng.uniform(-1, 1) * scale
        scale *= rough; step = h
    return base + pts
LW = W + 900       # layer width: room to pan
@functools.lru_cache(maxsize=32)
def layer_mask(base, amp, rough, seed):
    r = _ridge(2048, base, amp, rough, seed); xs = np.linspace(0, 2048, LW).astype(int).clip(0, 2048)
    ry = r[xs][None, :]; yy = np.arange(H, dtype="float32")[:, None]
    body = np.clip((yy - ry) * 1.0, 0, 1)
    rim = np.clip(1 - np.abs(yy - ry - 2) / 3, 0, 1) * (yy >= ry - 1)
    shade = np.clip((yy - ry) / 420, 0, 1)
    return (Image.fromarray((body * 255).astype("uint8")), Image.fromarray((rim * 255).astype("uint8")),
            Image.fromarray((body * shade * 255).astype("uint8")))
RIDGES = [  # base y, amplitude, roughness, seed, parallax, depth (0 near .. 1 far)
    (860, 120, .55, 3, .15, .85),
    (930, 150, .52, 5, .3, .62),
    (1030, 130, .5, 8, .5, .4),
    (1140, 110, .5, 12, .75, .2),
]
def ridges(L, mood, cam=0.0, mood2=None, k=0.0, layers=RIDGES, rim_col=None, rim_a=.5):
    hor = np.array(MOODS[mood][2], "float32")
    if mood2: hor = hor + (np.array(MOODS[mood2][2], "float32") - hor) * k
    for base, amp, rough, seed, par, depth in layers:
        body, rim, shade = layer_mask(base, amp, rough, seed)
        x0 = int(450 + cam * par); x0 = max(0, min(LW - W, x0))
        bm = body.crop((x0, 0, x0 + W, H)); rm = rim.crop((x0, 0, x0 + W, H)); sm = shade.crop((x0, 0, x0 + W, H))
        col = tuple(int(c) for c in np.array((8, 10, 18), "float32") * (1 - depth) + hor * depth * .55 + np.array((8, 10, 18)) * depth * .45)
        L.paste(Image.new("RGBA", (W, H), col + (255,)), (0, 0), bm)
        L.paste(Image.new("RGBA", (W, H), (4, 5, 9, 255)), (0, 0), sm.point(lambda v: int(v * .7)))
        rc = rim_col or mixc(MOON, tuple(int(c) for c in hor), .5)
        L.paste(Image.new("RGBA", (W, H), rc + (255,)), (0, 0), rm.point(lambda v: int(v * rim_a * (1 - depth * .6))))

@functools.lru_cache(maxsize=8)
def _fog(seed, w=1600, h=260):
    rng = np.random.default_rng(seed); m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m)
    for _ in range(26):
        x = rng.uniform(0, w); y = rng.uniform(h * .3, h * .7); rx = rng.uniform(120, 300); ry = rng.uniform(20, 50)
        d.ellipse((x - rx, y - ry, x + rx, y + ry), fill=int(rng.uniform(60, 140)))
    return m.filter(ImageFilter.GaussianBlur(28))
def fog(L, t, y, col=(120, 130, 160), a=.35, seed=1, speed=12):
    if a <= .01: return
    m = _fog(seed); x = int((t * speed) % 500)
    mm = m.crop((x, 0, x + W, m.height)).point(lambda v: int(v * a))
    L.paste(Image.new("RGBA", (W, m.height), col + (255,)), (0, int(y - m.height / 2)), mm)

# ---------- the pass: two near mountains and the gap ----------
G = 1270                       # ground at the gap
GAPL, GAPR = 420, 660          # gap at the ground
SLOPE = 170 / 560              # the gap widens upward
WTOP = 870
def gap_x(y): return GAPL - (G - y) * SLOPE, GAPR + (G - y) * SLOPE
@functools.lru_cache(maxsize=2)
def _pass_masks():
    rng = np.random.default_rng(21)
    def jag(pts, j=10):
        out = []
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(2, int(math.dist((x0, y0), (x1, y1)) / 22))
            for i in range(n): u = i / n; out.append((x0 + (x1 - x0) * u + rng.uniform(-j, j) * .4, y0 + (y1 - y0) * u + rng.uniform(-j, j)))
        out.append(pts[-1]); return out
    left = jag([(-80, 700), (40, 560), (140, 470), (230, 520), (300, 610), (GAPL - (G - 760) * SLOPE, 760), (GAPL, G)]) + [(GAPL, H), (-80, H)]
    right = jag([(GAPR, G), (GAPR + (G - 760) * SLOPE, 760), (800, 600), (880, 500), (960, 455), (1060, 520), (1160, 640)]) + [(1160, H), (GAPR, H)]
    S = 2; m = Image.new("L", (W * S, H * S), 0); d = ImageDraw.Draw(m)
    for poly in (left, right): d.polygon([(x * S, y * S) for x, y in poly], fill=255)
    m = m.resize((W, H), Image.LANCZOS)
    rim = Image.new("L", (W * S, H * S), 0); d = ImageDraw.Draw(rim)
    for poly in (left, right):
        top = [p for p in poly if p[1] < H - 5]
        d.line([(x * S, y * S + 3) for x, y in top], fill=255, width=5)
    rim = rim.resize((W, H), Image.LANCZOS)
    a = np.asarray(m).astype("float32") / 255
    shade = a * np.clip((_yy - 500) / 900, 0, 1) ** .8
    # strata lines on the faces
    st = Image.new("L", (W, H), 0); d = ImageDraw.Draw(st)
    for i in range(18):
        y = 560 + i * 44 + rng.uniform(-10, 10)
        d.line((-20, y, 380, y + rng.uniform(40, 90)), fill=60, width=2); d.line((700, y + 30, 1100, y - rng.uniform(20, 70)), fill=60, width=2)
    st = Image.fromarray((np.asarray(st).astype("float32") * a).astype("uint8")).filter(ImageFilter.GaussianBlur(1))
    ground = Image.new("L", (W, H), 0); ImageDraw.Draw(ground).rectangle((0, G - 2, W, H), fill=255)
    fine = np.asarray(Image.fromarray((rng.random((H // 3, W // 3)) * 255).astype("uint8")).resize((W, H), Image.BICUBIC)).astype("float32") / 255
    tex = a * np.clip((NOISE - .45) * 2.2 + (fine - .5) * .8, 0, 1)
    lit = a * np.where(_xx < 540, np.clip(_xx / 430, 0, 1) ** 2, np.clip((W - _xx) / 420, 0, 1) ** 2 * .35) * np.clip(1 - (_yy - 450) / 900, 0, 1)
    U8 = lambda z: Image.fromarray((np.clip(z, 0, 1) * 255).astype("uint8"))
    gl = np.clip((_yy - G) / 500, 0, 1) * (_yy >= G)
    return m, rim, U8(shade), st, ground, U8(tex), U8(lit), U8(gl)
def pass_mountains(L, mood, rim_col=None, light_k=0.0):
    m, rim, shade, st, ground, tex, lit, gl = _pass_masks()
    hor = MOODS[mood][2]
    L.paste(Image.new("RGBA", (W, H), mixc((11, 11, 15), hor, .1) + (255,)), (0, 0), ground)
    L.paste(Image.new("RGBA", (W, H), (5, 5, 8, 255)), (0, 0), gl)
    L.paste(Image.new("RGBA", (W, H), mixc((20, 22, 30), hor, .18) + (255,)), (0, 0), m)
    L.paste(Image.new("RGBA", (W, H), mixc((70, 74, 92), hor, .3) + (255,)), (0, 0), lit.point(lambda v: int(v * .55)))
    L.paste(Image.new("RGBA", (W, H), (96, 98, 112, 255)), (0, 0), tex.point(lambda v: int(v * .28)))
    if light_k > 0: L.paste(Image.new("RGBA", (W, H), (120, 52, 16, 255)), (0, 0), m.point(lambda v: int(v * .32 * light_k)))
    L.paste(Image.new("RGBA", (W, H), (60, 64, 76, 255)), (0, 0), st)
    L.paste(Image.new("RGBA", (W, H), (5, 6, 9, 255)), (0, 0), shade.point(lambda v: int(v * .85)))
    rc = rim_col or mixc(MOON, hor, .45)
    L.paste(Image.new("RGBA", (W, H), rc + (255,)), (0, 0), rim.point(lambda v: int(v * .7)))

# ---------- the wall ----------
def _blocks():
    out = []; rows = 10; rh = (G - WTOP) / rows
    for r in range(rows):
        y1 = G - r * rh; y0 = y1 - rh; xl, xr = gap_x(y0); xl -= 26; xr += 26
        n = max(3, round((xr - xl) / 92)); bw = (xr - xl) / n; off = (bw / 2) * (r % 2)
        xs = [xl - off + i * bw for i in range(n + (1 if r % 2 else 0))]
        for x in xs:
            a, b = max(x, xl), min(x + bw, xr)
            if b - a > 20: out.append((a, y0, b, y1))
    return out
BLOCKS = _blocks()
NB = len(BLOCKS)
_BR = np.random.default_rng(31)
BLOCK_V = [(_BR.uniform(-.08, .08), _BR.uniform(0, 1)) for _ in BLOCKS]
@functools.lru_cache(maxsize=2)
def _wall_mask():
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    for b in BLOCKS: d.rectangle(b, fill=255)
    return m, m.filter(ImageFilter.GaussianBlur(40)).point(lambda v: min(255, int(v * 1.6)))
def heat_col(h):
    stops = [(0, IRON), (.35, (110, 24, 12)), (.65, (226, 70, 18)), (.85, FIRE), (1, FHOT)]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if h <= b: return mixc(ca, cb, (h - a) / (b - a))
    return FHOT
def wall(L, t, build=1.0, heat=0.0, copper=0.0, fall=0.0, t_build=0.0, dur_build=1.0, drop=True):
    """build: 0..1 fraction of blocks placed (each drops in); heat: iron glow; copper: plating; fall: collapse."""
    d = ImageDraw.Draw(L, "RGBA")
    nshow = build * NB
    if heat > 0 and fall <= 0:
        gm = _wall_mask()[1]; L.paste(Image.new("RGBA", (W, H), FIRE + (255,)), (0, 0), gm.point(lambda v: int(v * .55 * heat)))
    for i, (x0, y0, x1, y1) in enumerate(BLOCKS):
        if i >= nshow: break
        k = _pin_(nshow - i) if drop else 1
        dy = -(1 - E("power2.in")(k)) * 260 if k < 1 else 0
        jit, rnd = BLOCK_V[i]
        h = _pin_(heat * (1 + jit * 2))
        base = heat_col(h)
        if copper > 0:
            rk = (G - y0) / (G - WTOP)
            cu = mixc((88, 46, 24), (178, 100, 50), .2 + .45 * rk + .25 * rnd); base = mixc(base, cu, copper)
        if fall > 0:
            cx = (x0 + x1) / 2; side = -1 if cx < 540 else 1
            f = _pin_(fall * 1.6 - (G - y1) / (G - WTOP) * .6 + rnd * .15)
            if f > 0:
                g = E("power2.in")(f)
                vx = side * (10 + 70 * rnd) * f; vy = g * (G - 12 - rnd * 50 - y1)
                rot = side * 70 * g * (.4 + rnd)
                cxp, cyp = cx + vx, (y0 + y1) / 2 + vy; hw, hh = (x1 - x0) / 2, (y1 - y0) / 2
                ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
                pts = [(cxp + ca * px - sa * py, cyp + sa * px + ca * py) for px, py in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
                d.polygon(pts, fill=mixc(base, (40, 36, 34), .45 * f) + (255,))
                continue
        yy0, yy1 = y0 + dy, y1 + dy
        d.rectangle((x0 + 1, yy0 + 1, x1 - 1, yy1 - 1), fill=base + (255,))
        hl = mixc(base, (255, 236, 210), .12 + .18 * copper); sh = mixc(base, (0, 0, 0), .4)
        d.rectangle((x0, yy0, x1, yy1), outline=mixc(base, (0, 0, 0), .7) + (255,), width=2)
        d.line((x0 + 3, yy0 + 3, x1 - 3, yy0 + 3), fill=hl + (200,), width=2)
        d.line((x0 + 3, yy1 - 3, x1 - 3, yy1 - 3), fill=sh + (255,), width=3)
        if copper > .3:   # specular streak
            sx = x0 + (x1 - x0) * (.2 + .6 * rnd)
            d.line((sx, yy0 + 5, sx - 6, yy1 - 5), fill=(255, 226, 180, int(150 * copper)), width=2)
        if k < 1 and k > .85: dust_puff(L, (x0 + x1) / 2, y1, (k - .85) / .15 * .4, 60)
    if fall <= 0 and nshow >= NB: wall_sheen(L, t, copper)

@functools.lru_cache(maxsize=4)
def _puff(r):
    return radial(r, (120, 108, 96), .55, 2.2)
WB = (int(gap_x(WTOP)[0]) - 40, WTOP - 10, int(gap_x(WTOP)[1]) + 40, G + 4)
@functools.lru_cache(maxsize=1)
def _wall_shade():
    m = np.asarray(_wall_mask()[0].crop(WB)).astype("float32") / 255
    yy, xx = np.mgrid[WB[1]:WB[3], WB[0]:WB[2]].astype("float32")
    dark = m * (np.clip((yy - WTOP) / (G - WTOP), 0, 1) ** 1.6 * .55 + np.clip(np.abs(xx - 540) / 300, 0, 1) ** 2 * .35)
    return m, dark, xx, yy
def wall_sheen(L, t, copper):
    m, dark, xx, yy = _wall_shade(); w, h = m.shape[1], m.shape[0]
    pos = 200 + ((t * 70) % 900) - 300
    band = m * np.exp(-((xx - WB[0] + (yy - WTOP) * .6 - pos) / 70) ** 2) * .28 * copper
    im = np.zeros((h, w, 4), "uint8"); im[..., :3] = 0; im[..., 3] = (dark * 255).astype("uint8")
    _i = Image.fromarray(im, "RGBA"); L.paste(_i, (WB[0], WB[1]), _i)
    if copper > 0:
        im2 = np.zeros((h, w, 4), "uint8"); im2[..., :3] = (255, 220, 180); im2[..., 3] = (np.clip(band, 0, 1) * 255).astype("uint8")
        _i = Image.fromarray(im2, "RGBA"); L.paste(_i, (WB[0], WB[1]), _i)
def dust_puff(L, x, y, k, r=120, col=None, a=.6):
    if k <= 0 or k >= 1: return
    rr = int(r * (.4 + 1.2 * E("power2.out")(k)))
    put(L, _puff(60), x, y - rr * .3, rr / 60, a * (1 - k))

def dust_cloud(L, t, t0, cx=540, cy=G, w=520, n=14, dur=3.2, a=.8):
    if t < t0 or t > t0 + dur: return
    q = (t - t0) / dur; rng = np.random.default_rng(5)
    for i in range(n):
        ox = rng.uniform(-1, 1) * w / 2; sp = rng.uniform(.6, 1.4); rr = rng.uniform(60, 130)
        k = _pin_(q * sp)
        put(L, _puff(60), cx + ox * (1 + .6 * k), cy - 30 - k * rng.uniform(60, 300), rr * (1.4 + 2.4 * k) / 60, a * (1 - k) * min(1, q * 8))

# ---------- fire, embers, copper ----------
def flames(L, t, k, x0=GAPL - 40, x1=GAPR + 40, y=G, hmax=230, n=13):
    if k <= 0: return
    light(L, (x0 + x1) / 2, y - 120, 520, FIRE, .5 * k)
    d = ImageDraw.Draw(L, "RGBA"); rng = np.random.default_rng(9)
    for col, sc in (((176, 30, 12), .95), ((240, 96, 20), .78), ((255, 178, 60), .55), ((255, 236, 180), .3)):
        for i in range(n):
            fx = x0 + (x1 - x0) * (i + .5) / n + rng.uniform(-8, 8)
            ph = rng.uniform(0, 6.3); sp = rng.uniform(5, 9)
            hh = hmax * k * sc * (.6 + .4 * math.sin(t * sp + ph) * math.sin(t * 2.3 + ph * 2))
            ww = (x1 - x0) / n * .95 * (sc + .1)
            sway = 10 * math.sin(t * 3 + ph)
            pts = [(fx - ww, y), (fx - ww * .6, y - hh * .45), (fx + sway, y - hh), (fx + ww * .6, y - hh * .45), (fx + ww, y)]
            d.polygon(pts, fill=col + (230,))
def embers(L, t, k, x0=GAPL - 60, x1=GAPR + 60, y=G, n=60, rise=900, seed=3, col=FIRE):
    if k <= 0: return
    rng = np.random.default_rng(seed); spr = dot_spr(3, col, 6)
    for i in range(n):
        x = rng.uniform(x0, x1); sp = rng.uniform(60, 180); ph = rng.uniform(0, rise); amp = rng.uniform(10, 40); w = rng.uniform(1, 3)
        h = (t * sp + ph) % rise; yy = y - h; xx = x + amp * math.sin(t * w + i)
        a = k * (1 - h / rise) * (.5 + .5 * math.sin(t * 7 + i))
        put(L, spr, xx, yy, rng.uniform(.5, 1.2), a)
def pour(L, t, k, streams=7, fade=1.0):
    """molten copper poured from above, running down the face of the wall"""
    if k <= 0 or fade <= 0: return
    d = ImageDraw.Draw(L, "RGBA"); rng = np.random.default_rng(17)
    xl, xr = gap_x(WTOP)
    for i in range(streams):
        x = xl + 30 + (xr - xl - 60) * (i + .5) / streams + rng.uniform(-12, 12)
        t0 = rng.uniform(0, .35); kk = _pin_((k - t0) / .5)
        if kk <= 0: continue
        top = WTOP - 290
        ln = (G - top) * kk; wv = rng.uniform(8, 14)
        # falling stream from above, then sheet running down the blocks
        pts = [(x + 3 * math.sin((top + s) * .03 + t * 6), top + s) for s in range(0, int(ln), 12)]
        if len(pts) > 1:
            d.line(pts, fill=COPPER + (int(240 * fade),), width=int(wv))
            d.line([(px - wv * .2, py) for px, py in pts], fill=COPPER_L + (int(220 * fade),), width=max(2, int(wv * .3)))
        light(L, x, min(G, top + ln), 120, (255, 150, 60), .35 * fade * kk)
    put(L, _crucible(), (xl + xr) / 2, WTOP - 305, 1, min(1, k * 4) * fade)
@functools.lru_cache(maxsize=1)
def _crucible():
    w = 380; im = Image.new("RGBA", (w, 70), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 10, w - 1, 60), 18, fill=(46, 40, 38, 255), outline=(120, 90, 70, 255), width=3)
    d.rectangle((14, 18, w - 14, 30), fill=COPPER_L + (255,))
    return glow(im, FIRE, 18, .6)

# ---------- dots (people are dots) ----------
SWARM_COL = (226, 82, 64)
def swarm(L, t, k, n=260, src=(540, 760), dst_y=(1180, 1500), spread=520, seed=7, col=SWARM_COL, alpha=1.0, r=5, flow=1.0, xr=(40, 1040)):
    """dots pour from src down over the land; k 0..1 how far they've come"""
    if k <= 0 or alpha <= 0: return
    d = ImageDraw.Draw(L, "RGBA"); rng = np.random.default_rng(seed)
    for i in range(n):
        delay = rng.uniform(0, .6); kk = _pin_((k - delay) / .4)
        if kk <= 0: continue
        tx = rng.uniform(*xr); ty = rng.uniform(*dst_y)
        sx = src[0] + rng.uniform(-spread / 2, spread / 2) * .3; sy = src[1] + rng.uniform(-30, 30)
        e = E("power2.inOut")(kk)
        x = sx + (tx - sx) * e + 6 * math.sin(t * 3 * flow + i); y = sy + (ty - sy) * e + 3 * math.cos(t * 4 * flow + i * 1.7)
        rr = r * (.7 + .6 * (y - 700) / 900)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=col + (int(255 * alpha * min(1, kk * 3)),))
def crowd(L, cx, cy, n, t, col=(236, 226, 204), spread=(120, 30), r=6, seed=3, a=1.0, glow_=False):
    d = ImageDraw.Draw(L, "RGBA"); rng = np.random.default_rng(seed)
    for i in range(n):
        x = cx + rng.normal(0, spread[0] / 2); y = cy + rng.normal(0, spread[1] / 2) + 2 * math.sin(t * 2 + i)
        d.ellipse((x - r, y - r, x + r, y + r), fill=col + (int(255 * a),))
    if glow_: light(L, cx, cy, spread[0] * 1.4, col, .25 * a)

# ---------- other drawings ----------
def sun(L, x, y, r, col, a=1.0):
    light(L, x, y, r * 7, col, .45 * a); light(L, x, y, r * 2.4, col, .8 * a)
    put(L, disc(r, mixc(col, (255, 250, 230), .5) + (255,)), x, y, 1, a)
def route(L, pts, k, col=HOT, gap=24, r=4):
    d = ImageDraw.Draw(L, "RGBA"); segs = []; tot = 0
    for a, b in zip(pts, pts[1:]): l = math.dist(a, b); segs.append((a, b, l)); tot += l
    s = 0; tip = pts[0]
    while s <= tot * k:
        acc = 0
        for a, b, l in segs:
            if s <= acc + l: u = (s - acc) / l; tip = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u); break
            acc += l
        d.ellipse((tip[0] - r, tip[1] - r, tip[0] + r, tip[1] + r), fill=col + (220,)); s += gap
    put(L, dot_spr(7, col, 10), tip[0], tip[1]); return tip

def rain(L, t, k, n=170, ang=.18, col=(170, 190, 220)):
    if k <= 0: return
    d = ImageDraw.Draw(L, "RGBA"); rng = np.random.default_rng(2)
    for i in range(n):
        x = rng.uniform(-200, W); sp = rng.uniform(1400, 2200); ph = rng.uniform(0, 2200); ln = rng.uniform(30, 60)
        y = (t * sp + ph) % 2100 - 100; xx = x + y * ang
        d.line((xx, y, xx + ln * ang, y + ln), fill=col + (int(150 * k),), width=2)

def bird(d, x, y, s, t, ph, col=(14, 14, 18)):
    f = math.sin(t * 7 + ph)
    wing = [(x - 70 * s, y - 40 * s * f), (x - 30 * s, y - 8 * s), (x, y), (x + 30 * s, y - 8 * s), (x + 70 * s, y - 40 * s * f)]
    d.line(wing, fill=col + (255,), width=max(3, int(9 * s)), joint="curve")
    d.line([(x, y), (x + 36 * s, y - 20 * s), (x + 64 * s, y - 52 * s)], fill=col + (255,), width=max(2, int(6 * s)), joint="curve")   # long neck
    d.ellipse((x + 58 * s, y - 60 * s, x + 74 * s, y - 46 * s), fill=col + (255,))
    d.ellipse((x - 18 * s, y - 8 * s, x + 22 * s, y + 10 * s), fill=col + (255,))

def lake_draw(L, cx, cy, rx, ry, level, t):
    """lake bed + water whose level (0..1) shrinks; cracks when dry"""
    d = ImageDraw.Draw(L, "RGBA")
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(46, 40, 34, 255))
    if level < .5:   # cracked bed
        rng = np.random.default_rng(4); a = int(200 * (1 - level * 2))
        for i in range(40):
            x = cx + rng.uniform(-rx * .8, rx * .8); y = cy + rng.uniform(-ry * .6, ry * .6)
            d.line((x, y, x + rng.uniform(-40, 40), y + rng.uniform(-12, 12)), fill=(24, 20, 16, a), width=2)
    if level > 0:
        wr, wy = rx * (.25 + .75 * level), ry * (.25 + .75 * level)
        d.ellipse((cx - wr, cy - wy, cx + wr, cy + wy), fill=WATER + (255,))
        d.ellipse((cx - wr * .9, cy - wy * .8, cx + wr * .9, cy + wy * .4), fill=mixc(WATER, (210, 230, 250), .25) + (255,))
        for i in range(5):
            yy = cy - wy * .3 + i * wy * .18; xx = cx + 30 * math.sin(t * .8 + i)
            d.line((xx - wr * .4, yy, xx + wr * .3, yy), fill=(230, 240, 255, 110), width=2)

def tur(L, k, glow_k=0.0, cx=540, base=1290, top=640, w=430):
    """at-Tur: one tall mountain (the place of refuge)"""
    if k <= 0: return
    y0 = base - (base - top) * E("power3.out")(k)
    d = ImageDraw.Draw(L, "RGBA"); rng = np.random.default_rng(41); pts = [(cx - w, base)]
    for i in range(1, 12):
        u = i / 12; x = cx - w + 2 * w * u; y = y0 + (base - y0) * (abs(u - .5) * 2) ** 1.25 + rng.uniform(-14, 14)
        pts.append((x, y))
    pts.append((cx + w, base))
    if glow_k > 0: light(L, cx, y0 + 30, 260, HOT, .6 * glow_k)
    mid = min(range(len(pts)), key=lambda i: pts[i][1]); sx, sy = pts[mid]
    d.polygon(pts[:mid + 1] + [(sx - 30, base)], fill=(40, 40, 50, 255))
    d.polygon(pts[mid:] + [(sx - 30, base)], fill=(20, 19, 25, 255))
    d.line(pts[1:-1], fill=mixc(MOON, HOT, glow_k) + (200,), width=3)
    return y0

def sprouts(L, k, t, y0=1300, n=60, seed=6):
    if k <= 0: return
    d = ImageDraw.Draw(L, "RGBA"); rng = np.random.default_rng(seed)
    for i in range(n):
        x = rng.uniform(20, W - 20); y = y0 + rng.uniform(0, 260); dl = rng.uniform(0, .5); kk = _pin_((k - dl) / .5)
        if kk <= 0: continue
        h = rng.uniform(20, 60) * kk * (1 + (y - y0) / 300); sw = 4 * math.sin(t * 2 + i)
        d.line((x, y, x + sw, y - h), fill=LEAF + (255,), width=3)
        d.ellipse((x + sw - 10 * kk, y - h - 4, x + sw, y - h + 4), fill=mixc(LEAF, (200, 230, 140), .3) + (255,))
        d.ellipse((x + sw, y - h * .7 - 4, x + sw + 10 * kk, y - h * .7 + 4), fill=LEAF + (255,))

@functools.lru_cache(maxsize=4)
def _pom(r):
    s = int(r * 2.6); yy, xx = np.mgrid[0:s, 0:s].astype("float32"); c = s / 2
    dd = np.sqrt((xx - c) ** 2 + (yy - c - r * .1) ** 2) / r
    inside = np.clip((1 - dd) * r / 2, 0, 1)
    lx = np.clip(1 - np.sqrt((xx - c + r * .35) ** 2 + (yy - c + r * .3) ** 2) / (r * .9), 0, 1)
    col = np.array(POM, "float32")[None, None] * (.55 + .45 * lx[..., None]) + np.array((255, 220, 220), "float32") * (lx ** 6)[..., None] * .6
    im = np.zeros((s, s, 4), "uint8"); im[..., :3] = np.clip(col, 0, 255); im[..., 3] = (inside * 255).astype("uint8")
    out = Image.fromarray(im, "RGBA"); d = ImageDraw.Draw(out)
    cw = r * .32; top = c - r * .9
    d.polygon([(c - cw, top + cw * .6), (c - cw * 1.1, top - cw * .5), (c - cw * .4, top), (c, top - cw * .7), (c + cw * .4, top), (c + cw * 1.1, top - cw * .5), (c + cw, top + cw * .6)], fill=(150, 26, 40, 255))
    return out
def pomegranate(L, x, y, r, k, split=0.0, t=0):
    if k <= 0: return
    p = _pom(r)
    if split <= 0: put(L, p, x, y, lerp(.6, 1, E("back.out(1.6)")(k)), k); return
    # split into two halves showing seeds
    hw = p.width // 2; lft = p.crop((0, 0, hw, p.height)); rgt = p.crop((hw, 0, p.width, p.height))
    o = split * r * .7
    seeds = Image.new("RGBA", p.size, (0, 0, 0, 0)); d = ImageDraw.Draw(seeds, "RGBA"); rng = np.random.default_rng(3); c = p.width / 2
    for i in range(140):
        a = rng.uniform(0, 6.28); rr = math.sqrt(rng.uniform(0, 1)) * r * .82
        sx, sy = c + math.cos(a) * rr * .45, c + r * .1 + math.sin(a) * rr
        d.ellipse((sx - 7, sy - 9, sx + 7, sy + 9), fill=(228, 40, 70, 255)); d.ellipse((sx - 3, sy - 6, sx + 1, sy - 2), fill=(255, 190, 200, 255))
    put(L, seeds, x, y, 1, min(1, split * 2))
    put(L, lft, x - hw / 2 - o, y, 1, 1, rot=12 * split); put(L, rgt, x + hw / 2 + o, y, 1, 1, rot=-12 * split)

def dome(L, x, y, r, k, col=POM):
    """the pomegranate's skin as a shade: a half shell"""
    if k <= 0: return
    d = ImageDraw.Draw(L, "RGBA"); rr = r * E("back.out(1.4)")(k)
    d.pieslice((x - rr, y - rr, x + rr, y + rr), 180, 360, fill=mixc(col, (80, 10, 20), .3) + (255,))
    d.arc((x - rr, y - rr, x + rr, y + rr), 190, 260, fill=(255, 140, 150, 200), width=6)
    d.ellipse((x - rr * 1.1, y + 4, x + rr * 1.1, y + 30), fill=(0, 0, 0, 110))

def ox_head(s=1.0, col=BONE):
    S = 3; w, h = int(260 * s), int(220 * s); im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    def P(pts): return [(x * s * S, y * s * S) for x, y in pts]
    d.polygon(P([(80, 70), (180, 70), (170, 160), (150, 205), (110, 205), (90, 160)]), outline=col + (255,), width=int(7 * S * s))
    d.line(P([(80, 76), (40, 60), (14, 22), (26, 10), (56, 52), (90, 66)]), fill=col + (255,), width=int(7 * S * s), joint="curve")
    d.line(P([(180, 76), (220, 60), (246, 22), (234, 10), (204, 52), (170, 66)]), fill=col + (255,), width=int(7 * S * s), joint="curve")
    d.line(P([(80, 84), (52, 98), (78, 110)]), fill=col + (255,), width=int(6 * S * s)); d.line(P([(180, 84), (208, 98), (182, 110)]), fill=col + (255,), width=int(6 * S * s))
    for ex in (110, 150): d.ellipse(P([(ex - 6, 110), (ex + 6, 122)]), fill=col + (255,))
    d.ellipse(P([(118, 178), (128, 188)]), fill=col + (255,)); d.ellipse(P([(132, 178), (142, 188)]), fill=col + (255,))
    return im.resize((w, h), Image.LANCZOS)
@functools.lru_cache(maxsize=1)
def OX(): return ox_head(.8)
@functools.lru_cache(maxsize=1)
def COIN():
    S = 3; im = Image.new("RGBA", (70 * S, 26 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, 70 * S - 1, 26 * S - 1), fill=COINC + (255,), outline=(150, 110, 40, 255), width=2 * S)
    d.ellipse((10 * S, 4 * S, 60 * S, 16 * S), outline=(255, 230, 170, 200), width=S)
    return im.resize((70, 26), Image.LANCZOS)
def balance(L, x, y, t, tilt_k, ox_k, coins_n):
    """a balance: ox head on the left, coins on the right; tilts toward the ox head"""
    ang = math.radians(-9 * tilt_k * (1 + .06 * math.sin(t * 2)))
    d = ImageDraw.Draw(L, "RGBA"); arm = 330
    d.polygon([(x - 34, y + 330), (x + 34, y + 330), (x + 6, y), (x - 6, y)], fill=(70, 66, 62, 255))
    d.line((x - 90, y + 332, x + 90, y + 332), fill=(90, 86, 80, 255), width=8)
    lx, ly = x - arm * math.cos(ang), y + arm * math.sin(ang); rx, ry = x + arm * math.cos(ang), y - arm * math.sin(ang)
    d.line((lx, ly, rx, ry), fill=STEEL + (255,), width=8); d.ellipse((x - 12, y - 12, x + 12, y + 12), fill=HOT + (255,))
    for px, py in ((lx, ly), (rx, ry)):
        d.line((px, py, px - 80, py + 170), fill=(150, 150, 160, 255), width=2); d.line((px, py, px + 80, py + 170), fill=(150, 150, 160, 255), width=2)
        d.chord((px - 110, py + 120, px + 110, py + 220), 0, 180, fill=(80, 76, 72, 255))
    if ox_k > 0: put(L, OX(), lx, ly + 100, lerp(.6, 1, E("back.out(1.6)")(ox_k)), ox_k)
    for i in range(coins_n):
        put(L, COIN(), rx + ((i % 3) - 1) * 52, ry + 158 - (i // 3) * 14, 1, 1)

def globe(L, x, y, r, t, k, col=BONE):
    if k <= 0: return
    S = 2; s = int(r * 2 + 8); im = Image.new("RGBA", (s * S, s * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s * S / 2; R_ = r * S
    a = int(220 * k)
    d.ellipse((c - R_, c - R_, c + R_, c + R_), outline=col + (a,), width=3 * S)
    for i in range(1, 6):
        yy = -R_ + 2 * R_ * i / 6; hw = math.sqrt(max(0, R_ * R_ - yy * yy)); d.line((c - hw, c + yy, c + hw, c + yy), fill=col + (a // 2,), width=S * 2)
    for i in range(6):
        ph = (t * .4 + i / 6 * math.pi) % math.pi; rx = abs(math.cos(ph)) * R_
        d.ellipse((c - rx, c - R_, c + rx, c + R_), outline=col + (a // 2,), width=S * 2)
    put(L, im.resize((s, s), Image.LANCZOS), x, y, lerp(.7, 1, E("back.out(1.5)")(k)), 1)

def strike(L, x, y, w, k, col=BLOOD):
    if k > 0: ImageDraw.Draw(L, "RGBA").line((x - w / 2, y, x - w / 2 + w * k, y), fill=col + (255,), width=6)

def beam(L, x, y_top, y_bot, k, col=HOT, w=120):
    if k <= 0: return
    m = Image.new("L", (int(w * 3), int(y_bot - y_top)), 0); d = ImageDraw.Draw(m)
    d.polygon([(w * 1.5 - w * .2, m.height), (w * 1.5 + w * .2, m.height), (w * 1.5 + w * .5, 0), (w * 1.5 - w * .5, 0)], fill=int(110 * k))
    m = m.filter(ImageFilter.GaussianBlur(24))
    L.paste(Image.new("RGBA", m.size, col + (255,)), (int(x - w * 1.5), int(y_top)), m)

def iris(L, cx, cy, r, a=.94):
    """darken everything outside a circle (the circle of the thumb and finger)"""
    m = Image.new("L", (W, H), int(255 * a)); ImageDraw.Draw(m).ellipse((cx - r, cy - r, cx + r, cy + r), fill=0)
    m = m.filter(ImageFilter.GaussianBlur(6))
    L.paste(Image.new("RGBA", (W, H), VOID + (255,)), (0, 0), m)
    d = ImageDraw.Draw(L, "RGBA"); d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=HOT + (230,), width=4)

def town(L, k=1.0, lamp=0.0, t=0):
    """Madinah at night as flat silhouettes: flat-roof houses, palms, one lit window"""
    if k <= 0: return
    d = ImageDraw.Draw(L, "RGBA"); rng = np.random.default_rng(12); col = (10, 11, 16, int(255 * k)); x = -20
    while x < W + 20:
        w = rng.uniform(70, 150); h = rng.uniform(80, 200); y = 1300 - h
        d.rectangle((x, y, x + w, 1340), fill=col)
        if rng.random() < .4: d.rectangle((x + w * .2, y - 18, x + w * .5, y), fill=col)
        x += w - 4
    for px in (130, 760, 980):
        d.line((px, 1300, px + 14, 1060), fill=col, width=12)
        for a in range(7):
            ang = -2.6 + a * .45; d.line((px + 14, 1060, px + 14 + 90 * math.cos(ang), 1060 + 50 * math.sin(ang) + 30), fill=col, width=9)
    if lamp > 0:
        wx, wy = 600, 1210
        light(L, wx, wy, 150, (255, 180, 90), .6 * lamp); d.rectangle((wx - 16, wy - 22, wx + 16, wy + 22), fill=(255, 196, 110, int(255 * lamp)))
    d.rectangle((0, 1340, W, H), fill=(6, 7, 10, 255))
