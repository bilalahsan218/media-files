"""Urdu narration, chunk by chunk, with measured timing. Reads script.py from the current folder:
  SCRIPT  = [(id, scene, speaker, urdu_caption, devanagari_for_tts, pause_after_s), ...]
  VOICES  = {"N": ("hm_omega", .95, "rubberband=pitch=0.93:formant=preserved"), ...}   (optional)
  SLOW    = {"s2b": .86, ...}   per-chunk speed overrides for names, Arabic phrases, short lines (optional)
  LEAD_IN = 1.0 ; GAP_SCALE = .85   (optional)
Each chunk is synthesised alone (Kokoro-82M, Hindi phonemes via espeak), trimmed with an energy gate, processed,
measured from its own samples and laid end to end with fixed pauses, so every chunk onset in timeline.json is
exact. Then run align.py (word times) and asr_check.py (Whisper read-back of every clip).
"""
import json, subprocess, os, importlib.util, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

SR = 24000
spec = importlib.util.spec_from_file_location("script", os.path.join(os.getcwd(), "script.py")); S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
VOICES = getattr(S, "VOICES", {"N": ("hm_omega", .95, "rubberband=pitch=0.93:formant=preserved"),
                               "C": ("hf_beta", .9, "rubberband=pitch=1.15:formant=shifted")})
SLOW = getattr(S, "SLOW", {}); LEAD_IN = getattr(S, "LEAD_IN", 1.0); GAP_SCALE = getattr(S, "GAP_SCALE", .85)
MODEL = os.path.expanduser("~/tts/kokoro-v1.0.onnx"); VOICEBIN = os.path.expanduser("~/tts/voices-v1.0.bin")

def trim(a, thr=0.012, pad=0.03):
    win = int(SR * .01); e = np.sqrt(np.convolve(a ** 2, np.ones(win) / win, "same")); idx = np.where(e > thr)[0]
    return a[max(0, idx[0] - int(pad * SR)):min(len(a), idx[-1] + int(pad * SR))]

def main():
    os.makedirs("clips", exist_ok=True)
    k = Kokoro(MODEL, VOICEBIN)
    pieces, chunks, t = [np.zeros(int(LEAD_IN * SR), "float32")], [], LEAD_IN
    for cid, scene, spk, ur, dv, gap in S.SCRIPT:
        voice, speed, fx = VOICES[spk]
        a, _ = k.create(dv, voice=voice, speed=SLOW.get(cid, speed), lang="hi"); a = trim(a.astype("float32"))
        raw, out = f"clips/{cid}_raw.wav", f"clips/{cid}.wav"; sf.write(raw, a, SR)
        if fx: subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", fx, "-ar", str(SR), out], check=True); os.remove(raw)
        else: os.replace(raw, out)
        a, _ = sf.read(out, dtype="float32"); a = trim(a); sf.write(out, a, SR); n = len(a) / SR
        uw = ur.split(); pw = k.tokenizer.phonemize(dv, "hi").split()
        if len(pw) != len(uw): pw = dv.replace("-", " ").split()
        wts = [max(1, len(w)) for w in pw][:len(uw)] + [3] * max(0, len(uw) - len(pw))
        cum = np.concatenate([[0], np.cumsum(wts)]) / sum(wts)
        words = [{"w": w, "start": round(t + n * cum[i], 3), "end": round(t + n * cum[i + 1], 3)} for i, w in enumerate(uw)]
        gap *= GAP_SCALE
        chunks.append({"id": cid, "scene": scene, "speaker": spk, "text": ur, "start": round(t, 3), "end": round(t + n, 3),
                       "dur": round(n, 3), "pause_after": round(gap, 3), "words_estimated": words})
        pieces += [a, np.zeros(int(gap * SR), "float32")]; t += n + gap
        print(f"{cid:5s} {spk} {t - n - gap:7.3f} {n:5.2f}  {ur}")
    v = np.concatenate(pieces); sf.write("voice_raw.wav", v, SR)
    json.dump({"sr": SR, "lead_in": LEAD_IN, "total": round(len(v) / SR, 3), "chunks": chunks}, open("timeline.json", "w"), ensure_ascii=False, indent=1)
    print("TOTAL", round(len(v) / SR, 2))

if __name__ == "__main__":
    main()
