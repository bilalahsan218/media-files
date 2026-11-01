"""Template reel using the NullMotion moves (ir_motion.py) in the Zamzam style. Copy, edit CONTENT.
Source verified on sunnah.com/bukhari:8 (Muhsin Khan translation, narrated by Ibn 'Umar)."""
import sys
from ir_motion import *

OUT = "NullMotion_Example.mp4"

SCENES = [
    # 1. Hook: manifesto title (words rise from masks with skew + blur, gold rule overshoots)
    manifesto_title("A HADITH ON THE FOUNDATION", ["WHAT IS ISLAM", "BUILT ON?"], "BUILT", "الإسلام"),
    # 2. Evidence: hub network, five pillars around one hub
    hub_scene("FIVE PILLARS", "ISLAM", ["Shahadah", "Salah", "Zakah", "Hajj", "Fasting"], ref="SAHIH AL-BUKHARI 8"),
    # 3. Evidence: pill morphs into the hadith page (direct quote, exact wording, with "...")
    morph_scene("Read the hadith", "NARRATED IBN 'UMAR (RA)",
                ["“Islam is based on (the following)", "five (principles)...”"],
                ref="SAHIH AL-BUKHARI 8", takeaway="Five pillars. One foundation."),
    # 4. End card: star pop, wipe, rule overshoot, pill glint + press ripple
    end_scene_nm("HADITH  ·  DID YOU KNOW?"),
]
STARTS = [0.0, 4.2, 9.6, 15.2]
DUR = 18.8
TRANS = [LIFT, ZOOM, flash]

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        print(render(SCENES, STARTS, DUR, TRANS, OUT, preview=[float(x) for x in sys.argv[2:]]))
    else:
        print(render(SCENES, STARTS, DUR, TRANS, OUT))
