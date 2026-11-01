"""ir_audio: synthesised sound design + the final mix for Islamic Reels.
Usage in a reel's sound.py:
    from reel import R                    # R = ir_urdu.run(...) result (B, DUR)
    from ir_urdu import ON, OFF, WT
    import ir_audio as A
    A.start(R["DUR"])
    A.wind(0, R["B"][1], .03); A.whoosh_all(R["B"]); A.thud(WT("s1b", 5), .3, 55, 1.0); A.chime(ON("s6a"), .12, 587)
    A.finish()                            # writes sfx.wav, voice_urdu.wav, mix.wav
Every effect is placed on the SAME measured cue times the animation uses, so sound, picture and voice share one clock.
Voice processing: the narrator pitch shift is already applied per clip in narrate.py, so finish() only adds warmth,
compression and loudness. The user's own track (nasheeds/main_track.mp3) sits at -9 dB, sidechain-ducked under the voice.
"""
import subprocess, os
import numpy as np, soundfile as sf

SR = 48000
_S = {"bed": None, "N": 0, "DUR": 0, "rng": np.random.default_rng(5)}
TRACK = os.path.expanduser("~/media-files/nasheeds/main_track.mp3")

def start(dur):
    _S["DUR"] = dur; _S["N"] = int(dur * SR) + SR; _S["bed"] = np.zeros(_S["N"], "float32")
def lp_fast(x, cutoff):
    k = max(1, int(SR / cutoff)); return np.convolve(x, np.ones(k) / k, "same").astype("float32")
def bp(x, lo, hi): return lp_fast(x, hi) - lp_fast(x, lo)
def env(n, a, r):
    e = np.ones(n, "float32"); na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e
def add(sig, t, gain):
    b = _S["bed"]; i = max(0, int(t * SR)); j = min(_S["N"], i + len(sig))
    if j > i: b[i:j] += sig[:j - i] * gain
def noise(sec): return _S["rng"].normal(0, 1, int(sec * SR)).astype("float32")

def wind(t0, t1, g):
    n = noise(max(.1, t1 - t0)); s = lp_fast(n, 500) - lp_fast(n, 90); tt = np.arange(len(s)) / SR
    add(s * (.6 + .4 * np.sin(2 * np.pi * tt / 7)) * env(len(s), 1.5, 1.5), t0, g)
def waves(t0, t1, g):
    n = noise(max(.1, t1 - t0)); s = bp(n, 200, 1400); tt = np.arange(len(s)) / SR
    add(s * (.55 + .45 * np.sin(2 * np.pi * tt / 5.3) * np.sin(2 * np.pi * tt / 3.1 + 1)) * env(len(s), 1.2, 1.2), t0, g)
def murmur(t0, t1, g):
    n = noise(max(.1, t1 - t0)); s = bp(n, 250, 900); tt = np.arange(len(s)) / SR
    add(s * (.5 + .5 * np.abs(np.sin(2 * np.pi * 3.1 * tt) * np.sin(2 * np.pi * 1.3 * tt + 1))) * env(len(s), 1.0, 1.2), t0, g)
def whoosh(t, g=.2):
    d = .7; n = noise(d); tt = np.linspace(0, 1, len(n)); add(bp(n, 300, 3000) * np.sin(np.pi * tt) ** 2, t - .3, g)
def whoosh_all(B, g=.2):
    """One whoosh at every scene boundary except the first and the end card."""
    for b in B[1:-1]: whoosh(b, g)
def thud(t, g=.3, f=58, d=.9):
    tt = np.arange(int(d * SR)) / SR; s = np.sin(2 * np.pi * f * tt * (1 - .3 * tt)) * np.exp(-tt * 5)
    s += .3 * lp_fast(noise(d), 200) * np.exp(-tt * 12); add(s.astype("float32"), t, g)
def tick(t, g=.1): thud(t, g, 120, .15)
def chime(t, g=.12, f=880):
    tt = np.arange(int(2.5 * SR)) / SR
    add(sum(np.sin(2 * np.pi * f * m * tt) * np.exp(-tt * (2 + m)) / m for m in (1, 2.01, 3.03)).astype("float32"), t, g)
def rustle(t, g=.1):
    d = .5; tt = np.linspace(0, 1, int(d * SR)); add(bp(noise(d), 1500, 6000) * np.sin(np.pi * tt) ** 2, t, g)
def pop(t, g=.12):
    d = .12; tt = np.arange(int(d * SR)) / SR; add((np.sin(2 * np.pi * 660 * tt * (1 + 2 * tt)) * np.exp(-tt * 40)).astype("float32"), t, g)
def riser(t_end, g=.12, d=1.2):
    """Soft rising swell that peaks exactly at t_end (use before a reveal, then silence)."""
    n = noise(d); tt = np.linspace(0, 1, len(n)); s = bp(n, 400, 4000) * tt ** 2.2
    add(s.astype("float32"), t_end - d, g)

def finish(track=TRACK, track_db=-9, voice_in="voice_raw.wav"):
    b = _S["bed"]; dur = _S["DUR"]
    b *= .9 / max(1e-6, np.abs(b).max()) * .6; sf.write("sfx.wav", b, SR)
    run = lambda c: subprocess.run(c, shell=True, check=True)
    run(f'ffmpeg -y -loglevel error -i {voice_in} -af "aresample=48000,highpass=f=70,equalizer=f=180:t=q:w=1:g=2.5,'
        'equalizer=f=3200:t=q:w=1.2:g=1.5,acompressor=threshold=-20dB:ratio=3:attack=8:release=120,'
        'loudnorm=I=-16:TP=-1.5:LRA=7" -ar 48000 voice_urdu.wav')
    run(f'ffmpeg -y -loglevel error -i voice_urdu.wav -t {dur} -i {track} -i sfx.wav -filter_complex '
        f'"[0:a]apad,atrim=0:{dur},asplit=2[v][vsc];[1:a]aresample=48000,volume={track_db}dB,afade=t=in:st=0:d=1.2,'
        f'afade=t=out:st={dur - 1.8}:d=1.8[m];[m][vsc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[md];'
        f'[2:a]atrim=0:{dur}[s];[v][md][s]amix=inputs=3:weights=1 0.55 1:normalize=0,alimiter=limit=0.9[a]" -map "[a]" -ar 48000 mix.wav')
    out = subprocess.run("ffmpeg -i mix.wav -af ebur128 -f null - 2>&1 | grep -E '^\\s+I:'", shell=True, capture_output=True, text=True).stdout
    print("mix.wav", out.strip())
