"""Whisper (Urdu) read-back of every narration clip, and a quick tester for pronunciation variants.
  python3 asr_check.py                 -> every clip in timeline.json: script text vs what Whisper hears
  python3 asr_check.py try "देवनागरी" ...  -> synthesise variants with the narrator voice and read them back
Clips are padded with 0.6 s of silence (Whisper drops the last word of unpadded clips)."""
import json, sys, os
import numpy as np, soundfile as sf
import sherpa_onnx
D = os.path.expanduser("~/tts/sherpa-onnx-whisper-small/")
R = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=D + "small-encoder.int8.onnx", decoder=D + "small-decoder.int8.onnx",
                                               tokens=D + "small-tokens.txt", language="ur", task="transcribe", num_threads=2)
def asr(a, sr):
    p = np.zeros(int(sr * .6), "float32"); s = R.create_stream(); s.accept_waveform(sr, np.concatenate([p, a.astype("float32"), p])); R.decode_stream(s)
    return s.result.text.strip()
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "try":
        from kokoro_onnx import Kokoro
        from narrate import trim, VOICES
        k = Kokoro(os.path.expanduser("~/tts/kokoro-v1.0.onnx"), os.path.expanduser("~/tts/voices-v1.0.bin"))
        v, sp, _ = VOICES["N"]
        for txt in sys.argv[2:]:
            for s_ in (sp, .86):
                a, sr = k.create(txt, voice=v, speed=s_, lang="hi"); print(f"{s_:.2f} {txt} | {asr(trim(a), sr)}")
    else:
        for c in json.load(open("timeline.json"))["chunks"]:
            a, sr = sf.read(f"clips/{c['id']}.wav", dtype="float32"); print(f"{c['id']:5s} {c['speaker']} | {c['text']} | {asr(a, sr)}")
