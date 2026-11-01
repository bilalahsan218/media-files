"""Template reel in the Zamzam style. Copy, then edit the CONTENT section."""
import math, sys
from PIL import Image, ImageDraw
from ir_doc import *

# ================= CONTENT =================
OUT = "Example_Reel.mp4"   # write to the working directory
TAG = "A MOTHER. A BABY. AN EMPTY VALLEY."
TITLE = ["HOW DID", "ZAMZAM BEGIN?"]
GOLD_WORD, TITLE_AR = "ZAMZAM", "زَمْزَم"
SRC = "SAHIH AL-BUKHARI  ·  3364"
# ===========================================

# --- scene 2: a document page that types out, highlights, circles and stamps a quote ---
DW, DH = 900, 760
DOC = paper(DW, DH, 71); ImageDraw.Draw(DOC).line((70, 118, DW - 70, 118), fill=LILAC + (255,), width=2)
DOC.alpha_composite(T(SRC, MONO(28), GOLD), (70, 60))
KICK = T("HER RESPONSE", ID("Black", 76), INK)
N1 = T("Ibrahim (AS) left her and baby Ismail", LO(38), INK)
N2 = T("there, by the command of Allah.", LO(38), INK)
Q1 = T("“Then He will not", LOI(70), INK); Q2 = T("neglect us.”", LOI(70), INK)
STAMP = stamp("SAHIH"); TAKE = T("Complete trust in Allah.", ID("Bold", 50), INK)
def s_doc(lt):
    L = desk(); k = eo5(p(lt, .1, .45))
    if k > 0: put(L, KICK, W / 2, 400 - 40 * (1 - k), 1, k)
    pg = DOC.copy()
    typed_on(pg, N1, 64, 160, c01((lt - .6) / .5)); typed_on(pg, N2, 64, 214, c01((lt - 1.0) / .45))
    highlight(pg, 70, 470, Q1.width - 20, 76, p(lt, 2.9, .5)); highlight(pg, 70, 560, Q2.width - 20, 76, p(lt, 3.1, .45))
    typed_on(pg, Q1, 64, 428, c01((lt - 2.0) / .5)); typed_on(pg, Q2, 64, 518, c01((lt - 2.45) / .4))
    marker_circle(pg, 70 + Q1.width / 2, 520, Q1.width / 2 + 50, 120, p(lt, 3.5, .55), width=6)
    sk = p(lt, 4.0, .25)
    if sk > 0: put(pg, STAMP, DW - 170, DH - 95, 1.5 - .5 * eo5(sk), c01(sk * 2))
    dk = eo5(p(lt, .1, .65))
    put(L, page_out(pg, -1.2), W / 2, 950 + 800 * (1 - dk), 1, 1, rot=5 * (1 - dk))
    if dk > 0:
        put(L, tape(190, 50, 4).rotate(-20, expand=True), W / 2 - 390, 590 + 800 * (1 - dk))
        put(L, tape(190, 50, 5).rotate(18, expand=True), W / 2 + 390, 590 + 800 * (1 - dk))
    tk = eo5(p(lt, 4.3, .5))
    if tk > 0: put(L, TAKE, W / 2, 1450 + 30 * (1 - tk), 1, tk)
    return L

# --- scene 3: a counter with hand-drawn tally marks and a taped quote card ---
CNT = {n: T(str(n), ID("Black", 150), INK) for n in range(1, 8)}
TIMES, TIME_ = T("TIMES", ID("Bold", 48), INK, track=6), T("TIME", ID("Bold", 48), INK, track=6)
CARD = paper(900, 270, 91)
LAB = SAW("THE PROPHET", MONO(23), GREY, "SAID")
CQ1 = T("“This is the source of the tradition of the", LOI(34), INK); CQ2 = T("walking of people between them.”", LOI(34), INK)
CR = T("SAHIH AL-BUKHARI 3364", MONO(23), GOLD)
def s_count(lt):
    L = desk(); leg0, leg = .6, .44
    done = int(c01((lt - leg0) / (leg * 7)) * 7)
    if done >= 1:
        pk = p(lt, leg0 + leg * 7, .4)
        put(L, hcat([CNT[done], TIME_ if done == 1 else TIMES], 24), W / 2, 700, (1 + .12 * math.sin(math.pi * pk)) if 0 < pk < 1 else 1)
        tally(L, W / 2 - 120, 830, done, eio(p(lt, leg0 + leg * done - .05, .18)))
    ck = eo5(p(lt, 4.0, .55))
    if ck > 0:
        cd = CARD.copy(); onto(cd, LAB, 60, 40, eo5(p(lt, 4.2, .4)))
        typed_on(cd, CQ1, 60, 100, c01((lt - 4.4) / .5)); typed_on(cd, CQ2, 60, 148, c01((lt - 4.8) / .4))
        onto(cd, CR, 60, 206, eo5(p(lt, 5.2, .4)))
        put(L, page_out(cd, 1.2, 16), W / 2 + 700 * (1 - ck), 1180, 1, 1, rot=-6 * (1 - ck))
    return L

SCENES = [title_scene(TAG, TITLE, GOLD_WORD, TITLE_AR), s_doc, s_count, end_scene()]
STARTS = [0.0, 3.8, 9.2, 15.4]
DUR = 19.0
TRANS = [WHIP_R, WHIP_L, flash]

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        print(render(SCENES, STARTS, DUR, TRANS, OUT, preview=[float(x) for x in sys.argv[2:]]))
    else:
        print(render(SCENES, STARTS, DUR, TRANS, OUT))
