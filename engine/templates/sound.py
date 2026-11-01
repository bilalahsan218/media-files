"""Template sound: every effect sits on a measured cue (same clock as the picture)."""
from reel import R
from ir_urdu import ON, OFF, WT
import ir_audio as A
A.start(R["DUR"])
A.wind(0, R["B"][1] + .3, .03)
A.whoosh_all(R["B"])
A.pop(WT("s1b", 7), .14)                       # the number lands
A.rustle(ON("s2a") + .2); A.chime(WT("s2b", 6), .1, 784)
A.riser(WT("s3a", 2), .1); A.thud(WT("s3a", 2) + .25, .35, 50, 1.2)
A.chime(R["B"][3] + .3, .1, 660)
A.chime(R["END_T"] + .3, .12, 660)
A.finish()
