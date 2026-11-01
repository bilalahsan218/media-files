"""Template: narrated Islamic Reel on the measured narration clock.
Structure: hook (karaoke question + big keyword) -> evidence (verified hadith card) -> the turn (spotlight stage)
-> takeaway + share line -> sources -> dark outro. Every cue is ON/OFF/WT/word_times, never a guessed number."""
import ir_urdu as U
from ir_urdu import *
from ir_viral import *
U.load("timeline.json")
U.KEY = {"بنیاد", "پانچ", "پہلی", "گواہی", "معبود", "رسول", "بھیجیں۔", "بخاری،"}
STAR = star8(18, GOLD)

def s1(t):   # HOOK: the question fills in as it is spoken; the answer lands as a giant number
    L = studio(); float_icons(L, t, STAR, 7, 5, area=(60, 1150, W - 60, 1420)); stage_hill(L, tw(t, .1, .8))
    karaoke(L, urdu_words("اسلام کی بنیاد کتنی چیزوں پر ہے؟", 58, INK, gold=("بنیاد",)), word_times("s1a"), W / 2, 440, t, 0, rtl=True, maxw=980)
    duo(L, hcat([TU("نے فرمایا", 44, GREY), T("ﷺ", FA(52), GOLD), TU("نبی کریم", 44, GREY)], 10), TU(un(5), 230, PURPLE), W / 2, 660, t, ON("s1b"), WT("s1b", 7))
    return L

CARD = QCard("SAHIH AL-BUKHARI 8", ["“Islam is based on (the following) five", "(principles): To testify that none has the",
             "right to be worshipped but Allah and", "Muhammad is Allah's Messenger...”"], "TRANSLATION: M. MUHSIN KHAN", 81, size=36,
             hl=[(1, "To testify", "the")])
def s2(t):   # EVIDENCE: the verified card types in while it is spoken; the key term gets a bar
    L = desk(); eyebrow(L, "THE FIRST PILLAR", t, R["B"][1] + .1)
    bar_word(L, TU("گواہی", 66, PAPER), W / 2, 470, t, WT("s2a", 5), PURPLE, rtl=True)
    CARD.draw(L, t, ON("s2a") + .2, 900, rot=-.6, t_hl=ON("s2b"), t_circ=WT("s2b", 6))
    return L

def s3(t):   # THE TURN: the stage darkens, a pawn becomes a king, light sweeps on the aha
    t0 = R["B"][2]
    L = studio(); checker_floor(L, tw(t, t0, .8, "power3.out"))
    for x in (W / 2 - 260, W / 2 + 260): put_fx(L, pawn(220, (30, 22, 40)), x, 1240, 1, None, 1, 0, 0, 0, "bottom")
    promote(L, W / 2, 1290, t, WT("s3a", 2))
    L = spotlight(L, tw(t, t0 + .2, .6))
    duo(L, TU("یہی ایک گواہی", 50, INK), TU("بنیاد", 150, PURPLE), W / 2, 330, t, ON("s3a"), WT("s3a", 4))
    return light_sweep(L, t, WT("s3a", 4) - .2)

TAKE = TU("ایمان کی بنیاد: ایک گواہی", 60, INK)
def s4(t):   # TAKEAWAY + SHARE: the screenshot card, then who to send it to
    L = desk(); eyebrow(L, "TAKEAWAY", t, R["B"][3] + .1)
    k = tw(t, R["B"][3] + .2, .6, "back.out(1.4)")
    if k > 0:
        pg = paper(900, 300, 401); pg.alpha_composite(TAKE, ((900 - TAKE.width) // 2, 50))
        sh = T("لَا إِلٰهَ إِلَّا اللّٰهُ مُحَمَّدٌ رَسُولُ اللّٰهِ", FA(50), GREY, ar=True); pg.alpha_composite(sh, ((900 - sh.width) // 2, 190))
        put(L, page_out(pg, -.8, 14), W / 2, 700 + 60 * (1 - k), 1, k)
    arc_sweep(L, W / 2, 700, 520, t, R["B"][3] + .6, 1.2, 160, 220, PURPLE, 4)
    ribbon(L, "SEND IT TO SOMEONE YOU LOVE", t, tw(t, ON("s4a"), .8, "power3.out"), -24, 1180)
    return L

def s5(t):   # SOURCES
    L = desk(); eyebrow(L, "SOURCE", t, R["B"][4] + .1)
    k = tw(t, R["B"][4] + .2, .6, "power4.out")
    if k > 0:
        pg = paper(900, 220, 501); pg.alpha_composite(TW("SAHIH AL-BUKHARI 8", MONO(34), GOLD), (50, 50))
        pg.alpha_composite(TW("Narrated by Ibn 'Umar (RA) · sunnah.com/bukhari:8", LOI(30), INK), (50, 120))
        put(L, page_out(pg, 0, 12), W / 2, 820 - 40 * (1 - k), 1, k)
    return L

R = run([s1, s2, s3, s4, s5], ["s2a", "s3a", "s4a", "s5a"], [WHIP_R, ZOOM, LIFT, PUSH_UP, None], None, tail=1.6, end_len=3.6, outro=dark_outro)
if __name__ == "__main__": cli(R)
