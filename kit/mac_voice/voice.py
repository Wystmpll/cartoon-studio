#!/usr/bin/env python3
"""Free, ElevenLabs-like narration on a Mac (Apple Silicon) with Qwen3-TTS (Apache-2.0), edge-tts as fallback.

Lives in the user's voice folder (e.g. ~/CartoonVoice). One-time setup: see setup.sh.

  python voice.py presets                         # list saved voices
  python voice.py design NAME "description" [--lang ru]   # create a voice from a text description, saves presets/NAME.wav+.txt
  python voice.py speak jobs/pN.json              # render every line of a job -> jobs/pN/l000.wav ...
  python voice.py test NAME "text" [--instruct "..."]      # quick audition -> test_NAME.wav

Job file (written by Claude):
  {"voice": "narrator_deep", "lang": "ru", "engine": "qwen-clone" | "qwen-design" | "edge",
   "lines": [{"text": "...", "instruct": "tense whisper"}, ...]}
qwen-clone : same timbre every line (cloned from the preset's reference clip) - most consistent
qwen-design: description + per-line emotion instruction - most expressive, timbre may drift slightly
edge       : Microsoft neural voices via edge-tts (free, needs internet)
"""
import json, os, sys, subprocess, shutil, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
PRESETS = os.path.join(HERE, "presets")
LANG = {"ru": "Russian", "en": "English"}
EDGE = {"ru": {"male": "ru-RU-DmitryNeural", "female": "ru-RU-SvetlanaNeural"}, "en": {"male": "en-US-GuyNeural", "female": "en-US-JennyNeural"}}

def qwen(args):
    exe = shutil.which("qwen-tts") or os.path.join(HERE, ".venv", "bin", "qwen-tts")
    cmd = [exe] + args + ["--no-play"] if "--no-play" in subprocess.run([exe, "--help"], capture_output=True, text=True).stdout else [exe] + args
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr); raise SystemExit(f"qwen-tts failed: {' '.join(args[:3])}...")

def design(name, desc, lang="ru", sample=None):
    os.makedirs(PRESETS, exist_ok=True)
    sample = sample or ("Если вы это слышите — значит, всё только начинается. Слушайте внимательно и не делайте резких движений."
                        if lang == "ru" else "If you can hear this, it has only just begun. Listen carefully and do not make any sudden moves.")
    out = os.path.join(PRESETS, f"{name}.wav")
    qwen([sample, "--design", "--instruct", desc, "-l", LANG[lang], "--model", "1.7B", "-o", out])
    open(os.path.join(PRESETS, f"{name}.txt"), "w").write(sample)
    json.dump({"desc": desc, "lang": lang}, open(os.path.join(PRESETS, f"{name}.json"), "w"), ensure_ascii=False)
    print("saved", out)

def line(job, ln, out):
    eng = job.get("engine", "qwen-clone"); lang = job.get("lang", "ru"); name = job.get("voice")
    if eng == "edge":
        v = job.get("edge_voice") or EDGE[lang][job.get("gender", "male")]
        rate = job.get("rate", "+0%")
        mp3 = out[:-4] + ".mp3"
        subprocess.run([shutil.which("edge-tts") or os.path.join(HERE, ".venv", "bin", "edge-tts"), "--voice", v, f"--rate={rate}",
                        "--text", ln["text"], "--write-media", mp3], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, out], check=True); os.remove(mp3); return
    meta = json.load(open(os.path.join(PRESETS, f"{name}.json")))
    if eng == "qwen-design":
        ins = meta["desc"] + (". " + ln["instruct"] if ln.get("instruct") else "")
        qwen([ln["text"], "--design", "--instruct", ins, "-l", LANG[lang], "--model", "1.7B", "-o", out])
    else:
        ref = os.path.join(PRESETS, f"{name}.wav"); ref_text = open(os.path.join(PRESETS, f"{name}.txt")).read()
        qwen([ln["text"], "--clone", ref, "--ref-text", ref_text, "-l", LANG[lang], "--model", job.get("model", "1.7B"), "-o", out])

def speak(jobfile):
    job = json.load(open(jobfile)); od = os.path.splitext(jobfile)[0]; os.makedirs(od, exist_ok=True)
    for i, ln in enumerate(job["lines"]):
        out = os.path.join(od, f"l{i:03d}.wav")
        if os.path.exists(out) and not job.get("redo") and i not in job.get("redo_lines", []): continue
        line(job, ln, out); print(f"[{i + 1}/{len(job['lines'])}] {ln['text'][:50]}", flush=True)
    open(os.path.join(od, "DONE"), "w").write("ok")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("a", nargs="?"); ap.add_argument("b", nargs="?")
    ap.add_argument("--lang", default="ru"); ap.add_argument("--instruct")
    x = ap.parse_args()
    if x.cmd == "presets":
        for f in sorted(os.listdir(PRESETS)) if os.path.isdir(PRESETS) else []:
            if f.endswith(".json"): print(f[:-5], "-", json.load(open(os.path.join(PRESETS, f)))["desc"])
    elif x.cmd == "design": design(x.a, x.b, x.lang)
    elif x.cmd == "speak": speak(x.a)
    elif x.cmd == "test":
        job = {"voice": x.a, "lang": x.lang, "engine": "qwen-design" if x.instruct else "qwen-clone"}
        line(job, {"text": x.b, "instruct": x.instruct}, os.path.join(HERE, f"test_{x.a}.wav")); print("ok")
