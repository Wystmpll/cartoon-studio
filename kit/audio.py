"""Background score + synthesized sound effects + final mix.

  python audio.py PROJ PART            -> PROJ/out/FINAL_p<PART>.mp4 (video + voice + music + sfx)

Music moods: tense, horror, sad, comedy, heroic, mystery, romance, calm.
SFX names (S.sfx(name, at) in scenes): whoosh, impact, thud, knock, steps, heartbeat, glass, door, buzz, typing, pop,
riser, sting, scream, groan, rotor, splash, punch, click, beep, alarm, crowd, wind, rain, boom, swoosh_up, ding, laugh_beep
"""
import json, os, sys, wave, subprocess, math
import numpy as np

SR = 48000
rng = np.random.default_rng(1)

def _t(d): return np.arange(int(d * SR)) / SR
def _env(n, a=0.005, r=None):
    e = np.ones(n); na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na)
    if r: nr = min(n, int(r * SR)); e[-nr:] *= np.linspace(1, 0, nr)
    return e
def _noise(d): return rng.standard_normal(int(d * SR))
def _lp(x, k=40):
    k = max(1, int(k)); return np.convolve(x, np.ones(k) / k, "same")
def _hp(x, k=40): return x - _lp(x, k)

def sfx(name):
    if name == "whoosh":
        d = 0.5; n = _noise(d); e = np.sin(np.linspace(0, np.pi, len(n))) ** 2
        return _lp(n, 12) * e * 0.9
    if name == "swoosh_up":
        d = 0.7; t = _t(d); return np.sin(2 * np.pi * (200 + 900 * t / d) * t) * np.sin(np.linspace(0, np.pi, len(t))) * 0.25 + _lp(_noise(d), 10) * np.linspace(0, 1, len(t)) * 0.5
    if name in ("impact", "boom"):
        d = 1.4 if name == "boom" else 0.8; t = _t(d)
        x = np.sin(2 * np.pi * (60 * np.exp(-t * 3)) * t) * np.exp(-t * (3 if name == "boom" else 6)) * 1.2 + _lp(_noise(d), 6) * np.exp(-t * 14) * 0.8
        return x
    if name == "thud":
        t = _t(0.35); return np.sin(2 * np.pi * 70 * t) * np.exp(-t * 18) * 1.1 + _lp(_noise(0.35), 30) * np.exp(-t * 30) * 0.6
    if name == "punch":
        t = _t(0.3); return _lp(_noise(0.3), 4) * np.exp(-t * 35) * 1.2 + np.sin(2 * np.pi * 90 * t) * np.exp(-t * 25)
    if name == "knock":
        out = np.zeros(int(1.2 * SR))
        for i in range(3):
            t = _t(0.12); k = (np.sin(2 * np.pi * 180 * t) + _lp(_noise(0.12), 8) * 0.6) * np.exp(-t * 60)
            s = int(i * 0.3 * SR); out[s:s + len(k)] += k
        return out
    if name == "steps":
        out = np.zeros(int(2.0 * SR))
        for i in range(5):
            t = _t(0.1); k = _lp(_noise(0.1), 15) * np.exp(-t * 50) * 0.7
            s = int(i * 0.38 * SR); out[s:s + len(k)] += k
        return out
    if name == "heartbeat":
        out = np.zeros(int(1.0 * SR))
        for off, a in ((0, 1.0), (0.22, 0.65)):
            t = _t(0.18); k = np.sin(2 * np.pi * 52 * t) * np.exp(-t * 22) * a
            s = int(off * SR); out[s:s + len(k)] += k
        return out
    if name == "glass":
        d = 1.0; t = _t(d); x = np.zeros(len(t))
        for f in (2400, 3100, 4100, 5200, 6100): x += np.sin(2 * np.pi * f * t + rng.random() * 6) * np.exp(-t * rng.uniform(5, 12))
        return x * 0.18 + _hp(_noise(d), 3) * np.exp(-t * 9) * 0.5
    if name == "door":
        t = _t(0.9); creak = np.sin(2 * np.pi * (300 + 80 * np.sin(t * 20)) * t) * 0.15 * np.sin(np.linspace(0, np.pi, len(t)))
        x = np.concatenate([creak, sfx("thud")]); return x
    if name == "buzz":
        out = np.zeros(int(1.0 * SR))
        for i in range(2):
            t = _t(0.3); k = np.sign(np.sin(2 * np.pi * 150 * t)) * 0.15 * _env(len(t), 0.01, 0.05)
            s = int(i * 0.45 * SR); out[s:s + len(k)] += _lp(k, 6)
        return out
    if name == "typing":
        out = np.zeros(int(1.2 * SR))
        for i in range(9):
            t = _t(0.03); k = _hp(_noise(0.03), 2) * np.exp(-t * 200) * 0.6
            s = int((i * 0.12 + rng.uniform(0, 0.04)) * SR); out[s:s + len(k)] += k
        return out
    if name == "pop":
        t = _t(0.15); return np.sin(2 * np.pi * (900 - 3000 * t) * t) * np.exp(-t * 30) * 0.6
    if name == "click":
        t = _t(0.05); return _hp(_noise(0.05), 2) * np.exp(-t * 150) * 0.7
    if name in ("beep", "ding"):
        t = _t(0.5); f = 1000 if name == "beep" else 1500
        return np.sin(2 * np.pi * f * t) * np.exp(-t * (8 if name == "ding" else 3)) * 0.35 * _env(len(t), 0.005, 0.05)
    if name == "riser":
        d = 2.0; t = _t(d); return (np.sin(2 * np.pi * (100 + 500 * (t / d) ** 2) * t) * 0.25 + _lp(_noise(d), 8) * 0.3) * (t / d) ** 2
    if name == "sting":
        t = _t(1.6); x = np.zeros(len(t))
        for f in (110, 116.5, 164.8, 233):
            x += np.sin(2 * np.pi * f * t) * np.exp(-t * 2.2)
        return x * 0.35 + _lp(_noise(1.6), 3) * np.exp(-t * 12) * 0.5
    if name == "scream":
        d = 1.0; t = _t(d); f0 = 520 + 120 * np.sin(t * 9)
        x = sum(np.sin(2 * np.pi * f0 * h * t) / h for h in (1, 2, 3, 4)) * 0.2
        return (x + _hp(_noise(d), 4) * 0.15) * np.sin(np.linspace(0, np.pi, len(t))) ** 0.5
    if name == "groan":
        d = 1.6; t = _t(d); f0 = 85 + 15 * np.sin(t * 3)
        x = sum(np.sin(2 * np.pi * f0 * h * t) / h for h in range(1, 7))
        return _lp(x, 20) * 0.35 * np.sin(np.linspace(0, np.pi, len(t)))
    if name == "rotor":
        d = 3.0; t = _t(d); return _lp(_noise(d), 30) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 11 * t))) * 0.9 * np.minimum(1, t)
    if name == "splash":
        t = _t(1.0); return _hp(_noise(1.0), 5) * np.exp(-t * 4) * 0.6 + _lp(_noise(1.0), 40) * np.exp(-t * 6) * 0.6
    if name == "alarm":
        t = _t(2.0); return np.sign(np.sin(2 * np.pi * (700 + 300 * (np.sin(2 * np.pi * 2 * t) > 0)) * t)) * 0.12
    if name == "crowd":
        d = 3.0; x = sum(sfx("groan")[:int(1.6 * SR)] for _ in range(1)); out = np.zeros(int(d * SR))
        for i in range(5):
            g = sfx("groan"); s = int(rng.uniform(0, 1.3) * SR); out[s:s + len(g)] += g * rng.uniform(0.4, 0.8)
        return out
    if name == "wind":
        d = 4.0; t = _t(d); return _lp(_noise(d), 60) * (0.6 + 0.4 * np.sin(t * 1.3)) * 2.0
    if name == "rain":
        d = 4.0; return _hp(_noise(d), 3) * 0.12
    if name == "laugh_beep":
        out = np.zeros(int(1.0 * SR))
        for i in range(4):
            t = _t(0.12); k = np.sin(2 * np.pi * (600 + i * 80) * t) * np.exp(-t * 20) * 0.3
            s = int(i * 0.15 * SR); out[s:s + len(k)] += k
        return out
    raise KeyError(f"unknown sfx {name}")

def music(dur, mood="tense", scene_starts=(), seed=1):
    r = np.random.default_rng(seed); n = int(dur * SR); t = np.arange(n) / SR
    out = np.zeros(n)
    def pad(freqs, amp=0.5, lfo=7.0):
        x = np.zeros(n)
        for f in freqs: x += np.sin(2 * np.pi * f * t + r.random() * 6) * (0.7 + 0.3 * np.sin(2 * np.pi * t / (lfo + f % 5)))
        return x * amp / len(freqs)
    def plucks(notes, every, amp=0.25, decay=6):
        x = np.zeros(n); k = 0; tt = 0.0
        while tt < dur:
            f = notes[k % len(notes)]; s = int(tt * SR); L = min(int(1.2 * SR), n - s)
            if L <= 0: break
            u = np.arange(L) / SR; x[s:s + L] += np.sin(2 * np.pi * f * u) * np.exp(-u * decay) * amp
            tt += every; k += 1
        return x
    if mood in ("tense", "horror"):
        out += pad([55, 82.4, 110, 164.8] if mood == "tense" else [55, 58.3, 82.4, 116.5], 0.9)
        out += _lp(rng.standard_normal(n), 400) * 3 * (0.6 + 0.4 * np.sin(2 * np.pi * t / 11))
        hb = dur * 0.6
        while hb < dur - 4:
            s = int(hb * SR); h = sfx("heartbeat")[:n - s]; out[s:s + len(h)] += h * 0.6; hb += 1.05
    elif mood == "sad":
        out += pad([110, 130.8, 164.8, 220], 0.6, 11) + plucks([440, 392, 349.2, 329.6], 1.6, 0.12, 2.5)
    elif mood == "comedy":
        out += plucks([392, 523.3, 440, 587.3, 392, 659.3], 0.32, 0.22, 9) + plucks([98, 130.8], 0.64, 0.25, 7)
    elif mood == "heroic":
        out += pad([98, 146.8, 196, 293.7], 0.6) + plucks([98, 98, 146.8, 98], 0.25, 0.25, 10)
    elif mood == "mystery":
        out += pad([73.4, 110, 155.6], 0.6) + plucks([880, 830.6, 659.3, 622.3], 1.1, 0.1, 3)
    elif mood == "romance":
        out += pad([130.8, 164.8, 196, 246.9], 0.55, 9) + plucks([523.3, 659.3, 784, 659.3], 0.8, 0.1, 2.5)
    else:  # calm
        out += pad([110, 164.8, 220], 0.5, 12)
    for st in scene_starts:
        s = int(st * SR); L = int(0.35 * SR)
        if 0 < s < n - L: out[s:s + L] += np.sin(2 * np.pi * 42 * np.arange(L) / SR) * np.exp(-np.linspace(0, 6, L)) * 0.7
    fade = np.minimum(1, np.minimum(t / 1.5, (dur - t) / 1.5)); out *= fade
    return out / (np.abs(out).max() + 1e-9) * 0.9

def write_wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())

def build_audio(proj, part):
    cfg = json.load(open(os.path.join(proj, "project.json"), encoding="utf-8"))
    tm = json.load(open(os.path.join(proj, "timing", f"p{part}.json"), encoding="utf-8"))
    dur = tm["duration"] + 0.3
    m = music(dur, cfg.get("music", "tense"), [s["start"] for s in tm["scenes"][1:]], seed=part)
    fx = np.zeros(len(m))
    cues_p = os.path.join(proj, "out", f"sfx_p{part}.json")
    if os.path.exists(cues_p):
        cache = {}
        for cu in json.load(open(cues_p)):
            if cu["name"] not in cache: cache[cu["name"]] = sfx(cu["name"])
            x = cache[cu["name"]]; s = int(cu["t"] * SR)
            if s >= len(fx): continue
            L = min(len(x), len(fx) - s); fx[s:s + L] += x[:L] * cu.get("vol", 1.0)
    os.makedirs(os.path.join(proj, "out"), exist_ok=True)
    write_wav(os.path.join(proj, "out", f"music_p{part}.wav"), m)
    write_wav(os.path.join(proj, "out", f"fx_p{part}.wav"), fx / (np.abs(fx).max() + 1e-9) * 0.9 if fx.any() else fx)
    return os.path.join(proj, "out", f"music_p{part}.wav"), os.path.join(proj, "out", f"fx_p{part}.wav")

def mix(proj, part, music_vol=0.18, fx_vol=0.55):
    mus, fxp = build_audio(proj, part)
    video = os.path.join(proj, "out", f"video_p{part}.mp4")
    voice = os.path.join(proj, "voice", f"p{part}.wav")
    if not os.path.exists(voice): voice = os.path.join(proj, "voice", f"p{part}_dev.wav")
    out = os.path.join(proj, "out", f"FINAL_p{part}.mp4")
    flt = (f"[1:a]aresample=48000,loudnorm=I=-15:TP=-1.5:LRA=11[v];[2:a]volume={music_vol}[m];[3:a]volume={fx_vol}[f];"
           f"[v][m][f]amix=inputs=3:duration=longest:normalize=0,alimiter=limit=0.95[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", voice, "-i", mus, "-i", fxp, "-filter_complex", flt,
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", out], check=True)
    return out

if __name__ == "__main__":
    print(mix(sys.argv[1], int(sys.argv[2])))
