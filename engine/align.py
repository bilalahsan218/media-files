"""Refine word timings inside each measured chunk.

Chunk onsets/ends in timeline.json are exact (measured from the samples). Inside a chunk, the first guess
for each word boundary is proportional to phoneme length; each internal boundary is then snapped to the
lowest-energy 10 ms frame within +-180 ms (the natural dip between words). Writes words_aligned per chunk.
"""
import json
import numpy as np, soundfile as sf

tl = json.load(open("timeline.json"))
for c in tl["chunks"]:
    a, sr = sf.read(f"clips/{c['id']}.wav", dtype="float32")
    hop = int(sr * .01); n = len(a) // hop
    rms = np.array([np.sqrt((a[i * hop:(i + 1) * hop] ** 2).mean()) for i in range(n)])
    rms = np.convolve(rms, np.ones(3) / 3, "same")
    ws = c["words_estimated"]; t0 = c["start"]
    bounds = [w["start"] - t0 for w in ws[1:]]
    snapped, last = [], 0.05
    for b in bounds:
        lo, hi = max(int((b - .18) * 100), int(last * 100) + 6), min(int((b + .18) * 100), n - 3)
        if hi <= lo: snapped.append(b); continue
        j = lo + int(np.argmin(rms[lo:hi])); snapped.append(j / 100); last = j / 100
    st = [0.0] + snapped; en = snapped + [c["dur"]]
    c["words_aligned"] = [{"w": w["w"], "start": round(t0 + s, 3), "end": round(t0 + e, 3)} for w, s, e in zip(ws, st, en)]
json.dump(tl, open("timeline.json", "w"), ensure_ascii=False, indent=1)
for c in tl["chunks"]:
    print(c["id"], " ".join(f"{w['w']}@{w['start']}" for w in c["words_aligned"]))
