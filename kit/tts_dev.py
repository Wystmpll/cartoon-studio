"""Draft narration with the free offline RHVoice synth (runs in the cloud workspace, no internet needed).
Used for timing previews before the real voice exists, or as a last-resort voice.

  python tts_dev.py PROJ PART [--lang ru|en] [--rate 125]

Needs: apt-get install -y rhvoice rhvoice-russian rhvoice-english ; stress marks: put '+' before the stressed vowel
in script.TTS_FIX (e.g. {"Нурали": "Нурал+и"}) - requires 'stress_marker=+' in /etc/RHVoice/RHVoice.conf (done automatically).
"""
import sys, os, subprocess, tempfile, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align

def ensure_rhvoice():
    if subprocess.run(["which", "RHVoice-test"], capture_output=True).returncode != 0:
        subprocess.run("apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -q rhvoice rhvoice-russian rhvoice-english", shell=True, check=True)
    conf = "/etc/RHVoice/RHVoice.conf"
    txt = open(conf).read() if os.path.exists(conf) else ""
    if "stress_marker=+" not in txt:
        open(conf, "w").write("stress_marker=+\n" + txt)

def speak(text, out, lang="ru", rate=125, pitch=86):
    voice = "aleksandr-hq" if lang == "ru" else "alan"
    subprocess.run(["RHVoice-test", "-p", voice, "-t", str(pitch), "-r", str(rate), "-o", out], input=text.encode(), check=True)

STEMS = {}
def fix(line, table):
    ws = line.split(); out = []
    for i, w in enumerate(ws):
        prev = ws[i - 1].lower() if i else ""
        core = w.rstrip(".,?!:;»"); tail = w[len(core):]
        if prev.startswith("блок") and core in ("С", "Б", "А"): out.append({"С": "Эс", "Б": "Бэ", "А": "А"}[core] + tail); continue
        if w in table or core in table:
            out.append(table.get(w) or table[core] + tail); continue
        for n, st in STEMS.items():
            if core.startswith(n) and len(core) - len(n) <= 3:
                out.append(st + core[len(n):] + tail); break
        else:
            out.append(w)
    return " ".join(out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("proj"); ap.add_argument("part", type=int)
    ap.add_argument("--lang", default="ru"); ap.add_argument("--rate", type=int, default=125)
    a = ap.parse_args()
    ensure_rhvoice()
    script = align.load_script(a.proj)
    table = dict(getattr(script, "TTS_FIX", {}))
    # stress hints from character libraries ("tts" field), applied to inflected forms too
    import json
    cfg = json.load(open(os.path.join(a.proj, "project.json"), encoding="utf-8"))
    libs = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "library", l + ".json") for l in cfg.get("libraries", [])]
    libs.append(os.path.join(a.proj, "characters.json"))
    STEMS = {}
    for p in libs:
        if os.path.exists(p):
            for n, spec in json.load(open(p, encoding="utf-8")).items():
                if spec.get("tts"): STEMS[n] = spec["tts"]
    d = tempfile.mkdtemp(); files = []; i = 0
    for sid, lines in script.PARTS[a.part]:
        for line in lines:
            f = os.path.join(d, f"l{i:03d}.wav"); speak(fix(line, table), f, a.lang, a.rate); files.append(f); i += 1
    words, audio, D = align.from_lines(script, a.part, files)
    align.save(a.proj, a.part, align.build_timing(script, a.part, words, D), audio, name=f"p{a.part}_dev.wav")
