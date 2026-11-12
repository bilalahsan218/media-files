# ==================================================================== scene kit
def base(t, mood, mood2=None, k=0.0, cam=0.0, moon_xy=None, moon_a=1.0, rid=True, fog_y=None, glow_x=540, star=True):
    L = sky(mood, mood2, k, glow_x)
    if star: stars(L, t, stars_of(mood, mood2, k))
    if moon_xy: moon(L, moon_xy[0], moon_xy[1], moon_a)
    if rid: ridges(L, mood, cam, mood2, k)
    if fog_y: fog(L, t, fog_y, mixc((120, 130, 160), MOODS[mood][2], .4), .3)
    return L
HDR = {1: ("ONE NIGHT", "SAHIH AL-BUKHARI 7059"), 2: ("THE WALL HAS OPENED", "BUKHARI 7059 · 3346"), 3: ("THE QUESTION", "AL-KAHF 18"),
       4: ("THE JOURNEYS", "AL-KAHF 18:83-93"), 5: ("THE REQUEST", "AL-KAHF 18:94-95"), 6: ("IRON, FIRE, COPPER", "AL-KAHF 18:96"),
       7: ("THE PROMISE", "AL-KAHF 18:97-98"), 8: ("EVERY ELEVATION", "AL-ANBIYA 21:96"), 9: ("WHEN?", "SAHIH MUSLIM 2937"),
       10: ("THE LAKE", "SAHIH MUSLIM 2937"), 11: ("BESIEGED", "SAHIH MUSLIM 2937"), 12: ("LIKE ONE SOUL", "SAHIH MUSLIM 2937"),
       13: ("THE EARTH RESTORED", "SAHIH MUSLIM 2937"), 14: ("REMEMBER", "QURAN · SUNNAH"), 15: ("ZAINAB'S QUESTION", "SAHIH AL-BUKHARI 7059"),
       16: ("HIS DECREE", "AL-KAHF 18:98"), 17: ("DUA", "")}
def fin(L, n, t):
    INV[0] = n == 17
    title, src = HDR[n]; chrome(L, n, title, src, t, ON(f"s{n}a") - .7); captions(L, t); return L
def scrim(L): L.paste(SCRIM, (0, 0), SCRIM); L.paste(HALF, (0, 0), HALF); return L
def ref(L, s, t, t0, y=1430, col=EMBER, until=None): return label(L, s, W / 2, y, t, t0, col, 20, until)
def hole(L, t, k, cx=540, cy=1080):
    if k <= 0: return
    r = 46 * E("back.out(1.6)")(k); light(L, cx, cy, 140 * k, EMBER, .7 * k)
    d = ImageDraw.Draw(L, "RGBA"); rng = np.random.default_rng(2); pts = []
    for i in range(14):
        a = i / 14 * 6.283; rr = r * (.75 + .5 * rng.random()); pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=(8, 4, 4, 255), outline=HOT + (255,))
    for i in range(6):   # glints of what is behind
        a = t * 2 + i; d.ellipse((cx + r * .4 * math.cos(a) - 3, cy + r * .3 * math.sin(a * 1.3) - 3, cx + r * .4 * math.cos(a) + 3, cy + r * .3 * math.sin(a * 1.3) + 3), fill=SWARM_COL + (255,))

def wall_world(t, mood="night", mood2=None, k=0.0, build=1.0, heat=0.0, copper=1.0, fall=0.0, light_k=0.0, behind=None, front=None, rid_cam=0.0, moon_xy=(900, 270)):
    L = base(t, mood, mood2, k, cam=rid_cam, moon_xy=moon_xy, moon_a=stars_of(mood, mood2, k))
    if behind: behind(L)
    wall(L, t, build, heat, copper, fall)
    pass_mountains(L, mood, light_k=light_k)
    if front: front(L)
    return L

@functools.lru_cache(maxsize=1)
def GROUND_M():
    a = np.clip((_yy - 1180) / 160, 0, 1) * .92
    return Image.fromarray((a * 255).astype("uint8"))

# ==================================================================== S1 one night
def s1(t):
    red = tw(t, WT("s1c", 3) - .2, 1.6)
    L = base(t, "night", "blood", red * .6, cam=-60, moon_xy=(800, 420), rid=False)
    town(L, 1, tw(t, WT("s1b", 8) - .1, .6), t)
    L = zoom(L, 1 + .05 * _pin_(t / 10), 600, 1200); scrim(L)
    forge(L, "ONE NIGHT", "cz", 118, W / 2, 520, t, WT("s1a", 0) - .1, BONE, track=6)
    k = tw(t, WT("s1b", 0) - .05, .6)
    if k > 0: put_fx(L, saw("THE MESSENGER OF ALLAH", 38), W / 2, 660 + 14 * (1 - k), 1, None, k, 0, 6 * (1 - k))
    gloss(L, "woke from his sleep", W / 2, 740, t, WT("s1b", 8) - .05, BONE, 46)
    forge(L, "HIS FACE FLUSHED RED", "cz", 60, W / 2, 860, t, WT("s1c", 3) - .05, BLOOD, track=3, hot=BLOOD)
    gloss(L, "and he was saying:", W / 2, 960, t, WT("s1d", 0) - .05, ASH, 40)
    return fin(L, 1, t)

# ==================================================================== S2 woe to the Arabs; this much has opened
def s2(t):
    if t < ON("s2d") - .25:
        L = base(t, "blood", cam=40, fog_y=1000); L = zoom(L, 1.04 - .04 * _pin_((t - ON("s2a")) / 7)); scrim(L)
        forge(L, "لَا إِلَٰهَ إِلَّا اللَّهُ", "ar", 104, W / 2, 450, t, ON("s2a") - .05, BONE, gr=16)
        ar_word(L, "وَيْلٌ لِلْعَرَبِ", "woe to the Arabs", W / 2, 690, t, WT("s2b", 0) - .05, HOT, 84)
        ar_word(L, "مِنْ شَرٍّ قَدِ اقْتَرَبَ", "from an evil that has come near", W / 2, 940, t, WT("s2c", 1) - .05, BLOOD, 84)
        ref(L, "SAHIH AL-BUKHARI 7059  ·  ZAINAB BINT JAHSH (RA)", t, ON("s2a") + .4, 1220)
        return fin(L, 2, t)
    hk = tw(t, WT("s2e", 2) - .1, .7)
    L = wall_world(t, "night", "blood", .5, moon_xy=None)
    hole(L, t, hk)
    zi = E("power2.inOut")(_pin_((t - ON("s2d") + .25) / 3.5))
    L = zoom(L, 1 + .35 * zi, 540, 1080)
    sh = tw(t, WT("s2f", 12) - .25, 1.3, "power3.inOut")
    if sh > 0:
        r = lerp(1300, 92, sh); iris(L, 540, 1080, r, .93)
    scrim(L)
    forge(L, "THE WALL OF YA'JUJ AND MA'JUJ", "cz", 44, W / 2, 470, t, WT("s2d", 5) - .05, BONE, until=WT("s2f", 12) - .4, track=2)
    forge(L, "A GAP HAS OPENED", "cz", 76, W / 2, 570, t, WT("s2e", 3) - .05, HOT, until=WT("s2f", 12) - .4, track=3)
    if sh > .2:
        forge(L, "THIS MUCH", "cz", 120, W / 2, 520, t, WT("s2f", 13) - .1, HOT, track=6)
        fade_text(L, "وَحَلَّقَ بِإِصْبَعِهِ الإِبْهَامِ وَالَّتِي تَلِيهَا", "ar", 48, W / 2, 1270, t, WT("s2f", 13) + .3, BONE)
        gloss(L, "and he made a circle with his thumb and the finger next to it", W / 2, 1345, t, WT("s2f", 13) + .5, ASH, 30)
        ref(L, "SAHIH AL-BUKHARI 3346", t, WT("s2f", 13) + .7, 1405)
    return fin(L, 2, t)

# ==================================================================== S3 which wall? who built it? who is behind it?
def s3(t):
    rev = tw(t, ON("s3e") - .1, 1.2)
    def behind(L):
        if rev > 0:
            light(L, 540, 760, 700, BLOOD, .45 * rev)
            swarm(L, t, rev, n=160, src=(540, 700), dst_y=(720, 860), spread=800, r=3, alpha=.8 * rev, xr=(180, 900))
    L = wall_world(t, "night", "blood", .7 * rev, behind=behind)
    fog(L, t, 1200, (90, 96, 120), .45 * (1 - rev * .5), 3, 20)
    L = zoom(L, 1.12 - .12 * E("power2.out")(_pin_((t - ON("s3a")) / 12)), 540, 1050); scrim(L)
    if t < ON("s3e") - .2:
        for i, (c, w, s) in enumerate([("s3a", 1, "WHICH WALL?"), ("s3b", 0, "WHO BUILT IT?"), ("s3d", 0, "WHO IS BEHIND IT?")]):
            forge(L, s, "cz", 70, W / 2, 400 + i * 120, t, WT(c, w) - .1, HOT if i == 2 else BONE, until=ON("s3e") - .45, track=3)
    else:
        forge(L, "يَأْجُوجُ وَمَأْجُوجُ", "ar", 132, W / 2, 430, t, WT("s3f", 0) - .1, HOT, gr=18)
        forge(L, "YA'JUJ AND MA'JUJ", "cz", 58, W / 2, 590, t, WT("s3f", 0) + .25, BONE, track=4)
        gloss(L, "known in English as Gog and Magog", W / 2, 660, t, WT("s3f", 2), ASH, 34)
    return fin(L, 3, t)

# ==================================================================== S4 Dhul-Qarnayn's journeys
def s4(t):
    if t < ON("s4d") - .25:
        L = base(t, "night", cam=0, moon_xy=(900, 270)); L = zoom(L, 1.03); scrim(L)
        globe(L, W / 2, 1000, 330, t, tw(t, WT("s4b", 3) - .1, .9) * .55, STEEL)
        label(L, "SURAH AL-KAHF  ·  18:83", W / 2, 360, t, WT("s4a", 1), EMBER, 22)
        forge(L, "ذُو الْقَرْنَيْنِ", "ar", 140, W / 2, 520, t, WT("s4a", 5) - .1, HOT, gr=18)
        forge(L, "DHUL-QARNAYN", "cz", 64, W / 2, 680, t, WT("s4a", 5) + .3, BONE, track=6)
        gloss(L, "We established him on the earth", W / 2, 1000, t, WT("s4b", 5) - .1, BONE, 46)
        ar_word(L, "سَبَبًا", "and gave him a way to everything", W / 2, 1150, t, WT("s4c", 4) - .1, HOT, 74)
        return fin(L, 4, t)
    if t < ON("s4h") - .25:
        tw_ = WT("s4d", 1); te = WT("s4e", 0); tm = WT("s4g", 1)
        ke = tw(t, te - .2, 2.2, "power2.inOut"); km = tw(t, tm - .2, 1.8, "power2.inOut")
        cam = lerp(lerp(-380 * tw(t, tw_ - .3, 2.5, "power2.inOut"), 380, ke), 0, km)
        gx = lerp(lerp(160, 920, ke), 540, km)
        mood, mood2, k = ("dusk", "dawn", ke) if km <= 0 else ("dawn", "night", km)
        L = sky(mood, mood2, k, int(gx)); stars(L, t, stars_of(mood, mood2, k))
        sx = tw(t, WT("s4d", 4), 2.2)
        sun(L, 200 - cam * .3, 700 + 160 * sx, 46, (190, 224, 40), (1 - ke))
        if ke > 0: sun(L, 880 - (cam - 380) * .3, 860 - 200 * ke, 46, (226, 255, 120), ke * (1 - km))
        ridges(L, mood, cam, mood2, k)
        if km > 0:
            ml = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pass_mountains(ml, "night")
            put(L, ml, W / 2, H / 2 + 700 * (1 - km), 1, min(1, km * 2))
        if ke <= 0: route(L, [(540, 1420), (130, 1380)], tw(t, tw_, 2.4))
        if ke > 0 and km <= 0: route(L, [(130, 1380), (950, 1380)], ke)
        if km > 0: route(L, [(950, 1380), (540, 1300)], km)
        scrim(L)
        label(L, "WEST", W / 2, 420, t, WT("s4d", 1), ASH, 22, until=te - .2)
        forge(L, "THE SETTING OF THE SUN", "cz", 54, W / 2, 490, t, WT("s4d", 5) - .1, BONE, until=te - .2, track=3)
        label(L, "EAST", W / 2, 420, t, te, ASH, 22, until=tm - .2)
        forge(L, "THE RISING OF THE SUN", "cz", 54, W / 2, 490, t, WT("s4e", 2) - .1, HOT, until=tm - .2, track=3)
        forge(L, "BETWEEN TWO MOUNTAINS", "cz", 54, W / 2, 330, t, WT("s4g", 2) - .1, BONE, track=3)
        ref(L, "AL-KAHF 18:86  ·  18:90  ·  18:93", t, WT("s4d", 5), 1460)
        return fin(L, 4, t)
    def front(L):
        crowd(L, 540, 1380, 26, t, (236, 214, 170), (300, 50), 6, 4, 1, True)
        for i in range(3):
            k = tw(t, WT("s4h", 4) + i * .35, .4, "back.out(1.6)")
            if k > 0: put(L, forged("?", "cg", 70, HOT)[0], 420 + i * 120, 1290 - 20 * (i % 2) - 10 * math.sin(t * 2 + i), k, k)
    L = wall_world(t, "night", build=0, front=front); L = zoom(L, 1.05, 540, 1200); scrim(L)
    forge(L, "A PEOPLE WHO COULD HARDLY", "cz", 50, W / 2, 420, t, WT("s4h", 4) - .1, BONE, track=2)
    forge(L, "UNDERSTAND SPEECH", "cz", 64, W / 2, 510, t, WT("s4h", 12) - .1, HOT, track=3)
    ref(L, "AL-KAHF 18:93  ·  SAHIH INTERNATIONAL", t, WT("s4h", 12) + .3, 1460)
    return fin(L, 4, t)

# ==================================================================== S5 the request
def s5(t):
    tc = WT("s5c", 0)
    def behind(L):
        if t < ON("s5d") + 1.3:
            a = 1 - tw(t, ON("s5d") + .6, .7)
            light(L, 540, 800, 520, BLOOD, .35 * tw(t, tc, 1) * a)
    def front(L):
        if t < ON("s5d") + 1.3:
            a = 1 - tw(t, ON("s5d") + .6, .7)
            swarm(L, t, tw(t, tc - .3, 2.0, "power1.out"), n=220, src=(540, 760), dst_y=(1290, 1440), spread=300, r=4, alpha=a, xr=(140, 940))
        crowd(L, 540, 1380, 26, t, (236, 214, 170), (300, 50), 6, 4, 1, True)
        kc = _pin_((t - WT("s5d", 6)) / 3.2) * (1 - tw(t, WT("s5f", 3), .6))
        n = int(18 * kc)
        for i in range(n): put(L, COIN(), 400 + (i % 6) * 56, 1330 - (i // 6) * 13, 1, kc)
        kd = tw(t, WT("s5h", 8) - .1, 1.6)
        if kd > 0:   # blueprint of the barrier
            d = ImageDraw.Draw(L, "RGBA")
            for i, (x0, y0, x1, y1) in enumerate(BLOCKS):
                kk = _pin_(kd * NB - i * .6)
                if kk > 0: d.rectangle((x0 + 3, y0 + 3, x1 - 3, y1 - 3), outline=HOT + (int(200 * kk),), width=2)
    L = wall_world(t, "night", "blood", .4 * tw(t, tc, 1) * (1 - tw(t, ON("s5f"), 1)), build=0, behind=behind, front=front)
    L = zoom(L, 1.06, 540, 1250); scrim(L)
    if t < ON("s5d") - .2:
        forge(L, "“O DHUL-QARNAYN!”", "cg", 82, W / 2, 400, t, WT("s5b", 0) - .1, BONE, until=ON("s5d") - .45)
        ar_word(L, "مُفْسِدُونَ", "Ya'juj and Ma'juj spread corruption in the land", W / 2, 560, t, WT("s5c", 5) - .1, BLOOD, 96, until=ON("s5d") - .45)
    elif t < ON("s5f") - .2:
        forge(L, "“MAY WE ASSIGN YOU", "cg", 68, W / 2, 390, t, WT("s5d", 0) - .1, BONE, until=ON("s5f") - .45)
        forge(L, "A PAYMENT?”", "cg", 68, W / 2, 470, t, WT("s5d", 6) - .1, GOLDC, until=ON("s5f") - .45)
        ar_word(L, "خَرْجًا", "a payment", W / 2, 620, t, WT("s5d", 6) + .2, GOLDC, 92, until=ON("s5f") - .45)
    else:
        forge(L, "“WHAT MY LORD HAS GIVEN ME", "cg", 62, W / 2, 380, t, WT("s5f", 0) - .1, BONE)
        forge(L, "IS BETTER”", "cg", 62, W / 2, 455, t, WT("s5f", 10) - .1, HOT)
        forge(L, "HELP ME WITH STRENGTH", "cz", 40, W / 2, 560, t, WT("s5g", 2) - .1, BONE, track=3)
        ar_word(L, "رَدْمًا", "a strong barrier", W / 2, 690, t, WT("s5h", 8) - .1, HOT, 92)
    ref(L, "AL-KAHF 18:94-95", t, ON("s5a"), 1465)
    return fin(L, 5, t)

# ==================================================================== S6 iron, fire, copper (18:96)
def s6(t):
    t0, t1 = WT("s6b", 1), WT("s6c", 12)
    build = _pin_((t - t0) / max(1, t1 - t0))
    fk = tw(t, WT("s6d", 1) - .1, .6) * (1 - tw(t, ON("s6f") + .3, .8))
    heat = _pin_((t - WT("s6d", 1)) / max(1, WT("s6e", 10) - WT("s6d", 1)))
    ck = _pin_((t - WT("s6f", 3)) / max(1, WT("s6g", 5) + .6 - WT("s6f", 3)))
    heat_v = heat * (1 - .8 * ck)
    def front(L):
        flames(L, t, fk); embers(L, t, max(fk, heat_v * .6), n=70)
        pour(L, t, ck, fade=1 - tw(t, WT("s6g", 6) + .6, .6))
    L = base(t, "night", "forge", min(1, heat + fk), moon_xy=(830, 330), moon_a=1 - min(1, heat + fk) * .6)
    wall(L, t, build, heat_v, ck)
    pass_mountains(L, "forge" if heat + fk > .5 else "night", light_k=max(fk, heat_v))
    front(L)
    zb = E("power2.inOut")(_pin_((t - ON("s6a")) / 20))
    L = zoom(L, 1.0 + .12 * zb, 540, 1080)
    dx, dy = shake(t, t1, 6, .4)
    if dx: L = L.transform(L.size, Image.AFFINE, (1, 0, dx, 0, 1, dy))
    scrim(L)
    ar_word(L, "زُبَرَ الْحَدِيدِ", "“bring me sheets of iron”", W / 2, 420, t, WT("s6b", 1) - .1, STEEL, 96, until=WT("s6c", 12) - .3)
    forge(L, "LEVEL BETWEEN THE TWO CLIFFS", "cz", 46, W / 2, 440, t, WT("s6c", 12) - .1, BONE, until=WT("s6d", 0) - .2, track=2)
    ar_word(L, "انفُخُوا", "“blow”  (on the fire, with bellows)", W / 2, 420, t, WT("s6d", 1) - .1, EMBER, 104, until=WT("s6e", 9) - .2)
    forge(L, "UNTIL IT WAS RED AS FIRE", "cz", 52, W / 2, 440, t, WT("s6e", 9) - .1, EMBER, until=WT("s6f", 4) - .2, track=2, hot=HOT)
    ar_word(L, "قِطْرًا", "molten copper", W / 2, 290, t, WT("s6f", 5) - .1, COPPER_L, 104, until=WT("s6g", 4) - .2)
    forge(L, "POURED OVER IT", "cz", 60, W / 2, 300, t, WT("s6g", 5) - .1, COPPER_L, track=4)
    ref(L, "AL-KAHF 18:96", t, ON("s6a"), 1465)
    return fin(L, 6, t)

# ==================================================================== S7 could not climb, could not pierce; mercy; levelled
def s7(t):
    tf = WT("s7e", 11); fall = _pin_((t - tf) / 2.0)
    def behind(L):
        if t < ON("s7d") - .2:
            d = ImageDraw.Draw(L, "RGBA"); rng = np.random.default_rng(9)
            for i in range(34):
                st = WT("s7b", 4) + rng.uniform(0, 2.5); p = ((t - st) * rng.uniform(.5, .9)) % 2.0
                if t < st: continue
                x = rng.uniform(gap_x(WTOP)[0] + 20, gap_x(WTOP)[1] - 20)
                up = math.sin(min(1, p / 1.2) * math.pi / 2) if p < 1.2 else 1 - E("power2.in")((p - 1.2) / .8)
                y = WTOP + 26 - 34 * up
                d.ellipse((x - 8, y - 8, x + 8, y + 8), fill=SWARM_COL + (255,))
    def front(L):
        if WT("s7b", 12) - .1 < t < ON("s7d"):
            rng = np.random.default_rng(3)
            for i in range(14):
                ph = rng.uniform(0, 1); per = rng.uniform(.5, .9); q = ((t + ph) % per) / per
                x = rng.uniform(GAPL + 10, GAPR - 10); y = rng.uniform(WTOP + 60, G - 30)
                if q < .25: light(L, x, y, 40, HOT, 1 - q * 4); put(L, dot_spr(3, WHITEHOT, 6), x, y, 1, 1 - q * 4)
        if t >= tf: dust_cloud(L, t, tf, 540, G, 700, 26, 3.8, .8)
    L = wall_world(t, "night", "gold", .35 * tw(t, ON("s7d"), .8) * (1 - tw(t, tf - .4, .6)), copper=1.0, fall=fall, behind=behind, front=front)
    dx, dy = shake(t, tf, 22, .9)
    if dx: L = L.transform(L.size, Image.AFFINE, (1, 0, dx, 0, 1, dy))
    L = zoom(L, 1.08 - .08 * E("power2.inOut")(_pin_((t - ON("s7d")) / 4)), 540, 1050); scrim(L)
    if t < ON("s7d") - .2:
        label(L, "THE QURAN SAYS", W / 2, 330, t, WT("s7a", 0), ASH, 22, until=ON("s7d") - .45)
        ar_word(L, "فَمَا اسْطَاعُوا أَن يَظْهَرُوهُ", "they were unable to climb it", W / 2, 440, t, WT("s7b", 7) - .1, BONE, 72, until=ON("s7d") - .45)
        ar_word(L, "وَمَا اسْتَطَاعُوا لَهُ نَقْبًا", "nor could they pierce it", W / 2, 660, t, WT("s7b", 13) - .1, HOT, 72, until=ON("s7d") - .45)
    elif t < ON("s7e") - .2:
        forge(L, "هَٰذَا رَحْمَةٌ مِّن رَّبِّي", "ar", 92, W / 2, 440, t, WT("s7d", 0) - .1, GOLDC, gr=16, until=ON("s7e") - .45)
        gloss(L, "“This is a mercy from my Lord”", W / 2, 560, t, WT("s7d", 4), BONE, 50, until=ON("s7e") - .45)
    else:
        gloss(L, "“but when the promise of my Lord comes”", W / 2, 360, t, WT("s7e", 5) - .1, BONE, 44, until=ON("s7f") - .3)
        ar_word(L, "دَكَّاءَ", "He will make it level", W / 2, 480, t, tf - .1, BLOOD, 120, until=ON("s7f") - .3)
        ar_word(L, "وَكَانَ وَعْدُ رَبِّي حَقًّا", "and the promise of my Lord is ever true", W / 2, 470, t, WT("s7f", 4) - .1, HOT, 84)
    ref(L, "AL-KAHF 18:97-98", t, ON("s7a"), 1465)
    return fin(L, 7, t)

# ==================================================================== S8 Al-Anbiya 21:96
def s8(t):
    tsw = WT("s8c", 3)
    L = base(t, "night", "blood", .5 * tw(t, tsw, 1.5), cam=lerp(-80, 80, _pin_((t - ON("s8a")) / 12)))
    swarm(L, t, tw(t, tsw - .2, 4, "power1.inOut"), n=320, src=(540, 880), dst_y=(1000, 1450), spread=1000, r=4, xr=(0, W))
    swarm(L, t, tw(t, tsw + .3, 4, "power1.inOut"), n=160, src=(160, 900), dst_y=(1050, 1450), spread=300, r=4, seed=9, xr=(0, 600))
    swarm(L, t, tw(t, tsw + .6, 4, "power1.inOut"), n=160, src=(920, 900), dst_y=(1050, 1450), spread=300, r=4, seed=10, xr=(480, W))
    scrim(L)
    if t < ON("s8b") - .2:
        forge(L, "SURAH AL-ANBIYA", "cz", 76, W / 2, 520, t, WT("s8a", 1) - .1, BONE, until=ON("s8b") - .4, track=5)
        label(L, "THE PROPHETS  ·  CHAPTER 21", W / 2, 610, t, WT("s8a", 1) + .4, EMBER, 22, until=ON("s8b") - .4)
        return fin(L, 8, t)
    forge(L, "حَتَّىٰ إِذَا فُتِحَتْ يَأْجُوجُ وَمَأْجُوجُ", "ar", 70, W / 2, 380, t, ON("s8b") - .05, BONE, gr=12)
    gloss(L, "until, when Ya'juj and Ma'juj have been opened", W / 2, 470, t, WT("s8b", 3), ASH, 36)
    forge(L, "وَهُم مِّن كُلِّ حَدَبٍ يَنسِلُونَ", "ar", 70, W / 2, 590, t, WT("s8c", 1) - .05, BONE, gr=12)
    gloss(L, "and they, from every elevation, descend", W / 2, 680, t, WT("s8c", 2), ASH, 36)
    ar_word(L, "حَدَبٍ", "every elevation", 300, 810, t, WT("s8c", 3), HOT, 70, en_size=30)
    ar_word(L, "يَنسِلُونَ", "they descend, pouring", 780, 810, t, WT("s8c", 5), BLOOD, 70, en_size=30)
    ref(L, "AL-ANBIYA 21:96  ·  SAHIH INTERNATIONAL", t, ON("s8b") + .4, 1465)
    return fin(L, 8, t)

# ==================================================================== S9 when? Sahih Muslim 2937
STEPS9 = [("s9d", 5, "ISA (AS) HAS DESCENDED"), ("s9d", 13, "THE DAJJAL IS KILLED"), ("s9e", 9, "ALLAH REVEALS TO ISA (AS)")]
def s9(t):
    if t < ON("s9f") - .2:
        L = base(t, "night", cam=120, moon_xy=(900, 270)); scrim(L)
        if t < ON("s9c") - .2:
            forge(L, "WHEN?", "cz", 170, W / 2, 520, t, WT("s9a", 1) - .1, HOT, track=8)
            kk = tw(t, WT("s9b", 1) - .05, 1.2, "power2.out")
            if kk > 0:
                n = int(2937 * kk); s = forged(f"{n}", "cz", 96, BONE, 4)[0]; put(L, s, W / 2, 760, 1, min(1, kk * 3))
                label(L, "SAHIH MUSLIM", W / 2, 680, t, WT("s9b", 1), EMBER, 24)
            gloss(L, "narrated by an-Nawwas ibn Sam'an (RA)", W / 2, 860, t, WT("s9b", 5), ASH, 38)
            return fin(L, 9, t)
        d = ImageDraw.Draw(L, "RGBA"); x = 250
        gloss(L, "it will be after...", W / 2, 380, t, ON("s9c") - .05, BONE, 48)
        kl = tw(t, WT("s9d", 5) - .3, 5.0, "power1.inOut")
        if kl > 0: d.line((x, 520, x, 520 + 480 * kl), fill=(80, 74, 68, 255), width=3)
        for i, (c, w, s) in enumerate(STEPS9):
            tt = WT(c, w) - .1; y = 540 + i * 220
            k = tw(t, tt, .5, "back.out(1.6)")
            if k > 0: diamond(L, x, y, 16 * k, HOT if i == 2 else EMBER); light(L, x, y, 60, EMBER, .5 * k)
            sp = forged(s, "cz", 40, HOT if i == 2 else BONE, 2)[0]
            forge(L, s, "cz", 40, x + 40 + sp.width / 2, y, t, tt, HOT if i == 2 else BONE, track=2)
        return fin(L, 9, t)
    if t < ON("s9h") - .2:
        L = base(t, "blood", cam=200); L = zoom(L, 1.0 + .05 * _pin_((t - ON("s9f")) / 6)); scrim(L)
        label(L, "ALLAH SAYS TO ISA (AS):", W / 2, 360, t, ON("s9f"), ASH, 22)
        forge(L, "لَا يَدَانِ لِأَحَدٍ بِقِتَالِهِمْ", "ar", 92, W / 2, 500, t, WT("s9f", 4) - .1, BLOOD, gr=16)
        gloss(L, "“I have brought forth servants of Mine", W / 2, 630, t, WT("s9f", 4) + .3, BONE, 46)
        gloss(L, "whom no one has the power to fight”", W / 2, 700, t, WT("s9g", 4) - .1, HOT, 46)
        return fin(L, 9, t)
    kt = tw(t, WT("s9i", 0) - .4, 1.4)
    L = base(t, "night", cam=200, moon_xy=(900, 270))
    y0 = tur(L, kt, tw(t, WT("s9j", 2), 1.2))
    kk = _pin_((t - WT("s9j", 2)) / 2.8); rng = np.random.default_rng(8); d = ImageDraw.Draw(L, "RGBA")
    if y0:
        for i in range(34):
            sx = rng.uniform(100, 980); ex = 540 + rng.uniform(-70, 70); ey = y0 + 40 + rng.uniform(0, 40)
            e = E("power2.inOut")(_pin_(kk * 1.3 - i / 60))
            x = lerp(sx, ex, e); y = lerp(1330, ey, e); d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(240, 232, 214, 255))
    d.rectangle((0, 1290, W, H), fill=(8, 8, 12, 255)); scrim(L)
    ar_word(L, "الطُّورِ", "at-Tur, the mountain", W / 2, 400, t, WT("s9i", 0) - .1, HOT, 110)
    gloss(L, "“so gather My servants safely to at-Tur”", W / 2, 600, t, WT("s9j", 4), BONE, 44)
    return fin(L, 9, t)

# ==================================================================== S10 every slope; Lake Tiberias
def s10(t):
    tl = WT("s10d", 13); lev = 1 - _pin_((t - tl) / 2.6)
    L = base(t, "night", "blood", .3, cam=-150, moon_xy=(900, 270))
    if t >= ON("s10d") - .4:
        k = tw(t, ON("s10d") - .4, .8); lk = Image.new("RGBA", (W, H), (0, 0, 0, 0)); lake_draw(lk, 540, 1210, 380, 80, lev, t); put(L, lk, W / 2, H / 2, 1, k)
    kk = tw(t, WT("s10b", 2) - .2, 4.5, "power1.inOut")
    if t < ON("s10d"): swarm(L, t, kk, n=340, src=(540, 880), dst_y=(1050, 1460), spread=1100, r=4, xr=(0, W))
    else: swarm(L, t, 1, n=340, src=(540, 880), dst_y=(1150, 1460), spread=1100, r=4, xr=(0, W), seed=7)
    L = zoom(L, 1.03 + .05 * _pin_((t - ON("s10d")) / 10), 540, 1210); scrim(L)
    if t < ON("s10d") - .2:
        forge(L, "ALLAH WILL SEND THEM", "cz", 52, W / 2, 420, t, WT("s10a", 7) - .1, BONE, track=2)
        forge(L, "DOWN EVERY SLOPE", "cz", 66, W / 2, 510, t, WT("s10b", 3) - .1, BLOOD, track=3)
        return fin(L, 10, t)
    ar_word(L, "بُحَيْرَةِ طَبَرِيَّةَ", "Lake Tiberias", W / 2, 380, t, WT("s10d", 4) - .1, WATER, 92, until=ON("s10e") - .3)
    forge(L, "THE FIRST OF THEM DRINK IT DRY", "cz", 44, W / 2, 600, t, WT("s10d", 15) - .1, BONE, until=ON("s10e") - .3, track=2)
    label(L, "THE LAST OF THEM WILL PASS AND SAY:", W / 2, 360, t, WT("s10e", 4), ASH, 22)
    forge(L, "لَقَدْ كَانَ بِهَذِهِ مَرَّةً مَاءٌ", "ar", 80, W / 2, 480, t, WT("s10g", 0) - .1, WATER, gr=14)
    gloss(L, "“There was once water here”", W / 2, 590, t, WT("s10g", 2), BONE, 50)
    return fin(L, 10, t)

# ==================================================================== S11 besieged; ox head > 100 dinars
def siege_world(t, tight, dead=0.0, mood="night", mood2="blood", k=.4, beam_k=0.0):
    L = base(t, mood, mood2, k, cam=200, moon_xy=(900, 270))
    y0 = tur(L, 1, .4 + .6 * beam_k)
    beam(L, 540, 0, y0 + 30, beam_k)
    crowd(L, 540, y0 + 60, 20, t, (240, 232, 214), (90, 20), 6, 3, 1, True)
    d = ImageDraw.Draw(L, "RGBA"); rng = np.random.default_rng(13)
    col = mixc(SWARM_COL, (70, 64, 60), dead)
    for i in range(420):
        a = rng.uniform(math.pi, 2 * math.pi) if i % 3 else rng.uniform(0, math.pi)
        rr = rng.uniform(0, 1)
        x = 540 + math.cos(rng.uniform(0, 6.28)) * (520 - 160 * tight * rr) * rng.uniform(.3, 1.1)
        y = lerp(1250, y0 + 160 + rr * 160, tight * rng.uniform(.4, 1)) + rng.uniform(-60, 40)
        x += 3 * math.sin(t * 3 + i) * (1 - dead); y += 2 * math.cos(t * 4 + i) * (1 - dead) + dead * 6
        if y < y0 + 120 or y > 1292: continue
        d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=col + (255,))
    d.rectangle((0, 1290, W, 1295), fill=(8, 8, 12, 255))
    return L
def s11(t):
    tight = tw(t, WT("s11b", 0) - .3, 1.5)
    L = siege_world(t, tight)
    bal = tw(t, WT("s11c", 8) - .2, .7)
    L = zoom(L, 1.05, 540, 900)
    if bal > 0: L = Image.blend(L, Image.new("RGB", (W, H), VOID), .62 * bal)
    scrim(L)
    if bal < 1:
        a = 1 - bal
        forge(L, "ISA (AS) AND HIS COMPANIONS", "cz", 40, W / 2, 380, t, ON("s11a"), HOT, track=2, alpha=a)
        forge(L, "BESIEGED", "cz", 110, W / 2, 500, t, WT("s11b", 0) - .1, BLOOD, track=8, alpha=a)
    if bal > 0:
        tilt = tw(t, WT("s11d", 5) - .1, 1.2, "back.out(2.2)")
        nc = int(12 * _pin_((t - WT("s11d", 2)) / 1.0))
        balance(L, W / 2, 640, t, tilt, tw(t, WT("s11c", 10) - .1, .5), nc)
        fade_text(L, "رَأْسُ الثَّوْرِ", "ar", 54, 230, 1090, t, WT("s11c", 10), BONE)
        gloss(L, "the head of an ox", 230, 1160, t, WT("s11c", 10) + .2, ASH, 34)
        kk = tw(t, WT("s11d", 2) - .05, 1.0, "power2.out")
        if kk > 0:
            put(L, forged(f"{max(1, int(100 * kk))}", "cz", 70, GOLDC, 2)[0], 850, 1020, 1, min(1, kk * 3))
            fade_text(L, "مِائَةِ دِينَارٍ", "ar", 54, 850, 1110, t, WT("s11d", 2) + .2, BONE)
            gloss(L, "a hundred dinars", 850, 1180, t, WT("s11d", 2) + .4, ASH, 34)
        forge(L, "WORTH MORE THAN", "cz", 44, W / 2, 400, t, WT("s11d", 5) - .1, HOT, track=3)
        ref(L, "SUCH WILL BE THEIR HUNGER  ·  SAHIH MUSLIM 2937", t, WT("s11d", 5) + .4, 1300)
    return fin(L, 11, t)

# ==================================================================== S12 worms; one death
def s12(t):
    tg = WT("s12c", 5); dead = tw(t, tg - .05, .35)
    bk = tw(t, WT("s12a", 13) - .2, 1.2) * (1 - tw(t, ON("s12b"), 1.0))
    L = siege_world(t, 1, dead, "blood" if dead <= 0 else "blood", "dead", dead, bk)
    if tg <= t < tg + .25: L = Image.blend(L, Image.new("RGB", (W, H), (236, 255, 190)), .35 * (1 - (t - tg) / .25))
    L = zoom(L, 1.05, 540, 900); scrim(L)
    if t < ON("s12b") - .2:
        forge(L, "ISA (AS) AND HIS COMPANIONS", "cz", 40, W / 2, 380, t, ON("s12a"), BONE, track=2, until=ON("s12b") - .4)
        forge(L, "TURN TO ALLAH", "cz", 84, W / 2, 480, t, WT("s12a", 13) - .1, HOT, track=5, until=ON("s12b") - .4)
        return fin(L, 12, t)
    ar_word(L, "النَّغَفَ", "worms in their necks", W / 2, 400, t, WT("s12b", 9) - .1, BLOOD, 110, until=ON("s12d") - .3)
    forge(L, "ALL AT ONCE", "cz", 52, W / 2, 620, t, WT("s12c", 2) - .1, BONE, until=ON("s12d") - .3, track=5)
    forge(L, "كَمَوْتِ نَفْسٍ وَاحِدَةٍ", "ar", 96, W / 2, 430, t, WT("s12d", 1) - .1, BONE, gr=16)
    gloss(L, "“like the death of a single soul”", W / 2, 550, t, WT("s12d", 3), ASH, 46)
    return fin(L, 12, t)

# ==================================================================== S13 the earth restored
def s13(t):
    tr = WT("s13f", 3); tg = WT("s13g", 7)
    rk = tw(t, tr - .3, .6) * (1 - tw(t, WT("s13g", 4), .8))
    mk = tw(t, tg - .6, 2.0)
    mood, mood2, k = ("dead", "storm", rk) if mk <= 0 else ("storm", "morning", mk)
    L = base(t, mood, mood2, k, cam=-100)
    d = ImageDraw.Draw(L, "RGBA")
    gc = mixc((34, 30, 26), (40, 64, 34), mk); L.paste(Image.new("RGBA", (W, H), gc + (255,)), (0, 0), GROUND_M())
    stain = tw(t, WT("s13b", 4), 1.0) * (1 - tw(t, WT("s13e", 4), 2.2))
    if stain > 0:
        rng = np.random.default_rng(14)
        for i in range(70):
            x = rng.uniform(0, W); y = rng.uniform(1260, 1500); r = rng.uniform(12, 40)
            d.ellipse((x - r, y - r * .35, x + r, y + r * .35), fill=(56, 40, 28, int(230 * stain)))
    if WT("s13a", 10) - .3 < t < ON("s13d"):   # they come down from the mountain
        kk = tw(t, WT("s13a", 10) - .3, 3)
        crowd(L, lerp(540, 300, kk), lerp(980, 1300, kk), 20, t, (240, 232, 214), (90, 20), 6, 3, 1)
    if ON("s13c") - .2 < t < ON("s13d") + .5: beam(L, 300, 600, 1300, tw(t, WT("s13c", 2), .8) * (1 - tw(t, ON("s13d"), .5)))
    if ON("s13d") - .3 <= t < ON("s13f"):
        dd = ImageDraw.Draw(L, "RGBA"); kb = t - WT("s13d", 4) + .4
        for i in range(5):
            x = -260 + (kb * 260 + i * 210) % 1600; y = 560 + i * 90 + 30 * math.sin(kb + i)
            bird(dd, x, y + 120, 1.6 + .2 * (i % 2), t, i * 1.3)
    rain(L, t, rk)
    if mk > 0: sun(L, 760, 1180 - 280 * mk, 50, (226, 255, 140), mk)
    sprouts(L, tw(t, tg - .1, 2.4), t, 1260)
    if t >= ON("s13h") - .3:
        kp = tw(t, WT("s13i", 1) - .2, .7); sp = tw(t, WT("s13i", 7) - .3, .8)
        pomegranate(L, 540, 860, 200, kp * (1 - tw(t, WT("s13i", 9), .5)), sp * (1 - tw(t, WT("s13i", 9), .5)), t)
        dk = tw(t, WT("s13i", 9) - .1, .8)
        if dk > 0:
            dome(L, 540, 1330, 260, dk); crowd(L, 540, 1310, 24, t, (240, 232, 214), (300, 20), 6, 5, dk)
        if t >= WT("s13h", 2) - .1: crowd(L, 540, 1310, 24, t, (240, 232, 214), (300, 20), 6, 5, 1 - dk)
    L = zoom(L, 1.03, 540, 1000); scrim(L)
    forge(L, "THEY COME DOWN TO THE EARTH", "cz", 44, W / 2, 400, t, ON("s13a"), BONE, until=WT("s13b", 4) - .3, track=2)
    forge(L, "NOT A HAND-SPAN OF EARTH SPARED", "cz", 44, W / 2, 400, t, WT("s13b", 4) - .1, BONE, until=ON("s13c") - .2, track=2)
    gloss(L, "from their fat and their stench", W / 2, 480, t, WT("s13b", 9), ASH, 40, until=ON("s13c") - .2)
    forge(L, "THEY CALL ON ALLAH", "cz", 64, W / 2, 400, t, WT("s13c", 2) - .1, HOT, until=ON("s13d") - .2, track=4)
    ar_word(L, "كَأَعْنَاقِ الْبُخْتِ", "birds with necks like Bactrian camels", W / 2, 360, t, WT("s13d", 9) - .1, BONE, 80, until=ON("s13e") - .2)
    forge(L, "CARRIED AWAY WHERE ALLAH WILLS", "cz", 42, W / 2, 400, t, WT("s13e", 5) - .1, BONE, until=ON("s13f") - .2, track=2)
    forge(L, "RAIN WASHES THE WHOLE EARTH", "cz", 46, W / 2, 400, t, WT("s13f", 3) - .1, BONE, until=ON("s13g") - .2, track=2)
    gloss(L, "“Bring forth your fruit,", W / 2, 380, t, WT("s13g", 6) - .1, BONE, 56, until=ON("s13h") - .3)
    gloss(L, "and restore your blessing”", W / 2, 450, t, WT("s13g", 10) - .1, HOT, 56, until=ON("s13h") - .3)
    ar_word(L, "الرُّمَّانَةِ", "one pomegranate feeds a whole group", W / 2, 360, t, WT("s13i", 1) - .1, (236, 96, 104), 88, until=WT("s13i", 7) - .2)
    ar_word(L, "بِقِحْفِهَا", "and they shade under its skin", W / 2, 360, t, WT("s13i", 7) - .1, (236, 96, 104), 88)
    ref(L, "SAHIH MUSLIM 2937", t, ON("s13a") + .3, 1470)
    return fin(L, 13, t)

# ==================================================================== S14 remember: the place is not named
def s14(t):
    L = base(t, "night", cam=-200, moon_xy=(900, 270)); scrim(L)
    globe(L, W / 2, 560, 230, t, tw(t, WT("s14a", 0) - .1, .9), STEEL)
    k = tw(t, WT("s14b", 7) - .05, .5, "back.out(1.6)")
    if k > 0: put(L, glow(forged("?", "cz", 260, HOT)[0], EMBER, 26, .6), W / 2, 560, lerp(1.5, 1, k), k)
    forge(L, "ITS LOCATION IS NOT GIVEN", "cz", 48, W / 2, 860, t, WT("s14b", 7) - .1, BONE, track=2)
    forge(L, "WITH CERTAINTY", "cz", 56, W / 2, 935, t, WT("s14b", 8) - .1, HOT, track=4)
    for i, (w, s) in enumerate([(3, "A COUNTRY"), (5, "A MOUNTAIN"), (10, "A PEOPLE OF TODAY")]):
        tt = WT("s14c", w) - .1
        if t < tt: continue
        a = 1 - .55 * tw(t, WT("s14c", 18), .3); y = 1060 + i * 82
        forge(L, s, "cz", 44, W / 2, y, t, tt, BONE, track=3, alpha=a)
        strike(L, W / 2, y, forged(s, "cz", 44, BONE, 3)[0].width, tw(t, WT("s14c", 19) - .1 + i * .12, .3))
    forge(L, "DON'T NAME ANYONE AS YA'JUJ AND MA'JUJ", "cz", 34, W / 2, 1340, t, WT("s14c", 19) + .2, BLOOD, track=1)
    return fin(L, 14, t)

# ==================================================================== S15 Zainab's question (Bukhari 7059)
def s15(t):
    L = base(t, "night", moon_xy=(900, 270), rid=False); town(L, 1, 1, t); L = zoom(L, 1.04, 600, 1200); scrim(L)
    if t < ON("s15b") - .2:
        gloss(L, "when he told of the wall opening,", W / 2, 400, t, ON("s15a"), BONE, 44)
        forge(L, "ZAINAB BINT JAHSH (RA)", "cz", 56, W / 2, 560, t, WT("s15a", 17) - .4, HOT, track=3)
        label(L, "MOTHER OF THE BELIEVERS", W / 2, 640, t, WT("s15a", 14), ASH, 22)
        gloss(L, "asked:", W / 2, 720, t, WT("s15a", 17), BONE, 44)
        return fin(L, 15, t)
    forge(L, "أَنَهْلِكُ وَفِينَا الصَّالِحُونَ", "ar", 86, W / 2, 330, t, WT("s15b", 5) - .1, BONE, gr=14)
    gloss(L, "“Shall we be destroyed", W / 2, 435, t, WT("s15b", 5) + .3, ASH, 42)
    gloss(L, "while the righteous are among us?”", W / 2, 490, t, WT("s15b", 12), ASH, 42)
    if t >= ON("s15c") - .2:
        k = tw(t, ON("s15c") - .1, .5)
        if k > 0: put_fx(L, saw("HE SAID", 34, BONE), W / 2, 600 + 12 * (1 - k), 1, None, k, 0, 5 * (1 - k))
        forge(L, "نَعَمْ", "ar", 170, W / 2, 745, t, WT("s15d", 0) - .1, HOT, gr=20, ember_hold=.0)
        gloss(L, "“Yes,", W / 2, 870, t, WT("s15d", 0) + .2, BONE, 48)
        forge(L, "إِذَا كَثُرَ الْخَبَثُ", "ar", 96, W / 2, 985, t, WT("s15e", 0) - .1, BLOOD, gr=16)
        gloss(L, "when evil increases”", W / 2, 1090, t, WT("s15e", 2), BONE, 48)
    return fin(L, 15, t)

# ==================================================================== S16 His decree
def s16(t):
    build = _pin_((t - ON("s16a")) / 2.6); tf = WT("s16c", 16); fall = _pin_((t - tf) / 2.0)
    L = wall_world(t, "night", "gold", .4 * tw(t, WT("s16c", 3), .8), build=build, copper=1.0, fall=fall,
                   front=lambda L: dust_cloud(L, t, tf, 540, G, 700, 26, 3.8, .8) if t >= tf else None)
    dx, dy = shake(t, tf, 20, .8)
    if dx: L = L.transform(L.size, Image.AFFINE, (1, 0, dx, 0, 1, dy))
    L = zoom(L, 1.02 + .06 * _pin_((t - ON("s16a")) / 15), 540, 1050); scrim(L)
    forge(L, "HOWEVER STRONG THE BARRIER", "cz", 48, W / 2, 420, t, WT("s16a", 4) - .1, BONE, until=ON("s16b") - .2, track=2)
    forge(L, "NO ONE CAN STOP", "cz", 50, W / 2, 380, t, WT("s16b", 8) - .3, BONE, until=ON("s16c") - .2, track=2)
    forge(L, "THE TIME ALLAH HAS SET", "cz", 56, W / 2, 470, t, WT("s16b", 4) - .1, HOT, until=ON("s16c") - .2, track=3)
    forge(L, "BUILT BY HIS COMMAND", "cz", 58, W / 2, 400, t, WT("s16c", 3) - .1, GOLDC, until=tf - .3, track=3)
    forge(L, "LEVELLED BY HIS COMMAND", "cz", 58, W / 2, 400, t, tf - .1, BLOOD, track=3)
    return fin(L, 16, t)

# ==================================================================== S17 dua
def s17(t):
    k = tw(t, ON("s17a") - .75, .9, "power2.inOut")
    L = base(t, "night")
    if k > 0: L = Image.blend(L, lime().convert("RGB"), k)
    L = zoom(L, 1.0 + .03 * _pin_((t - ON("s17a")) / 7), 540, 1000)
    L.paste(HALF, (0, 0), HALF)
    WG = (250, 255, 235)
    forge(L, "MAY ALLAH", "cz", 96, W / 2, 400, t, ON("s17a") - .1, INKD, track=6, hot=WG)
    forge(L, "GRANT US", "cz", 96, W / 2, 510, t, WT("s17a", 1) - .1, INKD, track=6, hot=WG)
    for i, (w, s) in enumerate([(2, "TRUE KNOWLEDGE"), (4, "FIRM IMAN"), (10, "PROTECTION FROM EVERY FITNAH")]):
        tt = WT("s17a", w) - .1; y = 660 + i * 92
        kk = tw(t, tt, .4)
        if kk > 0: diamond(L, W / 2, y - 46, 6 * kk, INKD, kk)
        forge(L, s, "cz", 40 if i == 2 else 46, W / 2, y, t, tt, INKD, track=2 if i == 2 else 3, hot=WG)
    ka = tw(t, ON("s17b") - .1, .45, "back.out(1.6)")
    if ka > 0: put(L, sticker("AMEEN", 96, INKD, LIME), W / 2, 1130, lerp(1.4, 1, ka), ka, rot=-4)
    return fin(L, 17, t)

# ==================================================================== outro
def outro(prev, t, t0):
    q = _pin_((t - t0) / .8)
    L = Image.blend(prev.convert("RGB"), Image.new("RGB", (W, H), VOID), .93 * E("power2.inOut")(q))
    forge(L, "ISLAMIC REELS", "cz", 92, W / 2, 820, t, t0 + .2, BONE, track=8)
    rule(L, W / 2, 900, 300, tw(t, t0 + .6, .6), EMBER)
    gloss(L, "Follow for more", W / 2, 960, t, t0 + .7, HOT, 46)
    gloss(L, "Send it to someone who reads Al-Kahf every Friday.", W / 2, 1050, t, t0 + 1.0, BONE, 40)
    return L

SC = [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15, s16, s17]
TR = [BURN, XF, BURN, XF, XF, XF, BURN, DIP, XF, XF, XF, XF, BURN, DIP, BURN, BURN, None]
R = U.run(SC, [f"s{i}a" for i in range(2, 18)], TR, None, tail=.6, end_len=2.4, push=0, caps=False, outro=outro)
R_END[0] = R["END_T"]
if __name__ == "__main__": cli(R)
