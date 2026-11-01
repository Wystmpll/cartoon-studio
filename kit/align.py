"""Turn narration audio into word timings for captions and scene cuts.

  python align.py PROJ PART AUDIO        # one long file (ElevenLabs mp3 etc.) -> pause-based alignment
  python align.py PROJ PART --lines DIR  # one wav per line (DIR/l000.wav, l001.wav ... in script order) -> exact

Writes PROJ/voice/p<PART>.wav (padded) and PROJ/timing/p<PART>.json. Prints segments so you can eyeball the match.
"""
import wave, json, re, sys, os, subprocess, importlib.util, glob
import numpy as np

SR = 24000
VOW = set("аеёиоуыэюяАЕЁИОУЫЭЮЯaeiouyAEIOUY")
LINE_GAP = 0.28; SCENE_GAP = 0.5; END_CARD = 4.0

def wweight(w):
    v = sum(ch in VOW for ch in w)
    if re.search(r"\d", w): v = 3
    return max(v, 0.6) + 0.35

def load_script(proj):
    spec = importlib.util.spec_from_file_location("script", os.path.join(proj, "script.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def read_audio(path):
    tmp = path + ".24k.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", str(SR), tmp], check=True)
    w = wave.open(tmp); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; os.remove(tmp)
    return a

def env_db(a, hop=120):
    fr = len(a) // hop
    e = np.sqrt(np.convolve(a[:fr * hop] ** 2, np.ones(hop) / hop, "same")[::hop])
    return 20 * np.log10(e + 1e-9)

def segments(a, min_gap=0.12, hop=120):
    db = env_db(a, hop); thr = np.percentile(db, 90) - 30; sp = db > thr
    segs = []; i = 0; fr = len(db)
    while i < fr:
        if sp[i]:
            j = i
            while j < fr and sp[j]: j += 1
            segs.append([i * hop / SR, j * hop / SR]); i = j
        else: i += 1
    out = [segs[0]]
    for s in segs[1:]:
        if s[0] - out[-1][1] < min_gap: out[-1][1] = s[1]
        else: out.append(s)
    out2 = []
    for s in out:
        if s[1] - s[0] < 0.07 and out2: out2[-1][1] = s[1]
        else: out2.append(s)
    return out2, db

def flatten(script, part):
    words = []
    for si, (sid, lines) in enumerate(script.PARTS[part]):
        for li, line in enumerate(lines):
            toks = line.split()
            for ti, w in enumerate(toks):
                if w in ("—", "-", "–"): continue
                nxt_dash = ti + 1 < len(toks) and toks[ti + 1] in ("—", "–")
                words.append(dict(w=w, si=si, li=li, dash=nxt_dash, last=ti == len(toks) - 1))
    return words

def distribute(words, k0, k1, s, e, cum, wt, db, hop=120):
    pieces = [k0]
    for k in range(k0 + 1, k1):
        if words[k - 1]["w"].endswith((".", "?", "!", ",", ":", "»")) or words[k - 1]["dash"]: pieces.append(k)
    pieces.append(k1)
    tot = cum[k1] - cum[k0]; cuts = [s]
    for p in pieces[1:-1]:
        pred = s + (e - s) * (cum[p] - cum[k0]) / tot
        lo = max(cuts[-1] + 0.1, pred - 0.45); hi = min(e - 0.1, pred + 0.45)
        if db is None or hi <= lo: cuts.append(pred); continue
        i0, i1 = int(lo * SR / hop), int(hi * SR / hop)
        cuts.append((i0 + int(np.argmin(db[i0:i1]))) * hop / SR if i1 > i0 else pred)
    cuts.append(e)
    for pi in range(len(pieces) - 1):
        a0, a1 = pieces[pi], pieces[pi + 1]; ps, pe = cuts[pi], cuts[pi + 1]
        if pi > 0: ps += 0.04
        if pi < len(pieces) - 2: pe -= 0.04
        tt = cum[a1] - cum[a0]; cur = ps
        for k in range(a0, a1):
            dd = (pe - ps) * wt[k] / tt
            words[k]["s"] = round(cur, 3); words[k]["e"] = round(cur + dd, 3); cur += dd

def align_long(words, a, verbose=True):
    K = len(words)
    wt = np.array([wweight(x["w"]) for x in words]); cum = np.concatenate([[0], np.cumsum(wt)])
    def pen(k):
        x = words[k - 1]
        if x["last"] or x["w"].endswith((".", "?", "!", "»")): return 0.0
        if x["w"].endswith((",", ":")) or x["dash"]: return 0.35
        return 3.0
    segs, db = segments(a); M = len(segs)
    r = sum(e - s for s, e in segs) / cum[-1]
    INF = 1e18
    f = np.full((M + 1, K + 1), INF); bk = np.zeros((M + 1, K + 1), int); f[0][0] = 0
    for j in range(1, M + 1):
        d = segs[j - 1][1] - segs[j - 1][0]; tol = 0.18 + 0.2 * d
        for k in range(1, K + 1):
            pk = pen(k) if k < K else 0.0; best = INF; bi = 0
            for k0 in range(max(0, k - 45), k):
                if f[j - 1][k0] >= INF: continue
                cst = f[j - 1][k0] + ((d - r * (cum[k] - cum[k0])) / tol) ** 2 + pk
                if cst < best: best, bi = cst, k0
            f[j][k] = best; bk[j][k] = bi
    if f[M][K] >= INF:
        raise RuntimeError("alignment failed: the audio probably does not match the script text (check the part number / edits)")
    bounds = []; k = K
    for j in range(M, 0, -1):
        k0 = bk[j][k]; bounds.append((k0, k)); k = k0
    bounds.reverse()
    for j, (k0, k1) in enumerate(bounds):
        s, e = segs[j]
        distribute(words, k0, k1, s, e, cum, wt, db)
        if verbose: print(f"{s:6.2f}-{e:6.2f}  " + " ".join(x["w"] for x in words[k0:k1]))
    print(f"segments {M}, words {K}, cost {f[M][K]:.1f}  (cost per segment > 1.5 means check the printout)")
    return len(a) / SR

def build_timing(script, part, words, total_audio):
    scenes = []; first = {}
    for x in words: first.setdefault(x["si"], x["s"])
    for si, (sid, lines) in enumerate(script.PARTS[part]):
        if not lines: start = scenes[-1]["_last"] + 0.7
        else: start = 0.0 if si == 0 else max(0, first[si] - 0.12)
        sc = {"id": sid, "start": start, "lines": []}
        for li, line in enumerate(lines):
            ws = [dict(w=x["w"], s=x["s"], e=x["e"]) for x in words if x["si"] == si and x["li"] == li]
            sc["lines"].append({"text": line, "start": ws[0]["s"], "end": ws[-1]["e"], "words": ws})
        sc["_last"] = sc["lines"][-1]["end"] if lines else start
        scenes.append(sc)
    for i in range(len(scenes) - 1): scenes[i]["end"] = scenes[i + 1]["start"]
    if PARTS_HAS_END(script, part): total = scenes[-1]["start"] + END_CARD
    else: total = max(total_audio, scenes[-1]["_last"]) + 0.8
    scenes[-1]["end"] = total
    for sc in scenes: sc.pop("_last", None)
    return {"duration": total, "scenes": scenes}

def PARTS_HAS_END(script, part):
    return not script.PARTS[part][-1][1]

def save(proj, part, timing, a, name=None):
    os.makedirs(os.path.join(proj, "timing"), exist_ok=True); os.makedirs(os.path.join(proj, "voice"), exist_ok=True)
    json.dump(timing, open(os.path.join(proj, "timing", f"p{part}.json"), "w"), ensure_ascii=False, indent=1)
    n = int(timing["duration"] * SR); a = np.concatenate([a, np.zeros(max(0, n - len(a)), np.float32)])[:n]
    with wave.open(os.path.join(proj, "voice", name or f"p{part}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())
    print("duration", round(timing["duration"], 1))

def from_lines(script, part, files):
    """files: one audio per script line, in order. Gaps are inserted here, so timings are exact per line."""
    words = flatten(script, part)
    chunks = []; t = 0.35; out = [np.zeros(int(0.35 * SR), np.float32)]; fi = 0
    for si, (sid, lines) in enumerate(script.PARTS[part]):
        for li, line in enumerate(lines):
            a = read_audio(files[fi]); fi += 1
            db = env_db(a); thr = np.percentile(db, 90) - 32; idx = np.where(db > thr)[0]
            a = a[max(0, idx[0] * 120 - 240): idx[-1] * 120 + 480]
            D = len(a) / SR
            lw = [k for k, x in enumerate(words) if x["si"] == si and x["li"] == li]
            wt = np.array([wweight(words[k]["w"]) for k in lw]); cum = np.concatenate([[0], np.cumsum(wt)])
            sub = [words[k] for k in lw]
            distribute(sub, 0, len(sub), t, t + D, cum, wt, None)
            out.append(a); t += D
            gap = LINE_GAP if li < len(lines) - 1 else SCENE_GAP
            out.append(np.zeros(int(gap * SR), np.float32)); t += gap
    if fi != len(files): print(f"warning: {len(files)} files for {fi} lines")
    a = np.concatenate(out)
    return words, a, len(a) / SR

if __name__ == "__main__":
    proj, part = sys.argv[1], int(sys.argv[2])
    script = load_script(proj)
    if sys.argv[3] == "--lines":
        files = sorted(glob.glob(os.path.join(sys.argv[4], "l*.wav")) + glob.glob(os.path.join(sys.argv[4], "l*.mp3")))
        words, a, D = from_lines(script, part, files)
    else:
        a = read_audio(sys.argv[3]); words = flatten(script, part); D = align_long(words, a)
    save(proj, part, build_timing(script, part, words, D), a)
