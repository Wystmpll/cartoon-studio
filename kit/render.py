"""Render a cartoon project.

  python render.py PROJ PART                 -> PROJ/out/pPART/*.mp4 per scene + PROJ/out/video_pPART.mp4 (silent)
  python render.py PROJ PART --only id1 id2  -> re-render only those scenes, keep the rest
  python render.py PROJ PART --stills id:0.5 id2:0.9   -> PNG stills in PROJ/out/stills/
  python render.py PROJ PART --style comic   -> override style (for style tests)

PROJ layout: project.json, script.py, scenes_p<N>.py, timing/p<N>.json, [characters.json]
"""
import json, sys, os, subprocess, math, importlib.util, random
import numpy as np
import cairo
KIT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, KIT)
from engine import *
import engine, styles, captions, chars, world

def load_project(proj, style_override=None):
    cfg = json.load(open(os.path.join(proj, "project.json"), encoding="utf-8"))
    for lib in cfg.get("libraries", []):
        p = lib if os.path.exists(lib) else os.path.join(KIT, "..", "library", lib + ".json")
        chars.load_library(p)
    pc = os.path.join(proj, "characters.json")
    if os.path.exists(pc): chars.load_library(pc)
    engine.LANG["code"] = cfg.get("lang", "ru")
    st = styles.apply(style_override or cfg.get("style", "survival"))
    captions.CAP.clear(); captions.CAP.update(st["cap"])
    spec = importlib.util.spec_from_file_location("script", os.path.join(proj, "script.py"))
    script = importlib.util.module_from_spec(spec); spec.loader.exec_module(script)
    yel = set(getattr(script, "KEY_YEL", ())) | {n for n in chars.P}
    captions.set_keywords(getattr(script, "KEY_RED", ()), yel)
    return cfg, st, script

def load_scenes(proj, part):
    sys.path.insert(0, proj)
    spec = importlib.util.spec_from_file_location(f"scenes_p{part}", os.path.join(proj, f"scenes_p{part}.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

class S:
    """Per-scene helper passed to scene functions: S.dur, S.L(i) line start, S.w('word') word start, S.sfx(...)."""
    def __init__(self, sc, cues):
        self.sc = sc; self.t0 = sc["start"]; self.dur = sc["end"] - sc["start"]; self._sm = {}; self._cues = cues
    def L(self, i):
        ls = self.sc["lines"]
        return ls[min(i, len(ls) - 1)]["start"] - self.t0 if ls else 0.0
    def Le(self, i):
        return self.sc["lines"][i]["end"] - self.t0
    def w(self, frag, n=0, default=None):
        frag = frag.lower(); k = 0
        for ln in self.sc["lines"]:
            for wd in ln["words"]:
                if wd["w"].lower().strip("—.,?!:;«»\"").startswith(frag):
                    if k == n: return wd["s"] - self.t0
                    k += 1
        if default is not None: return default
        raise KeyError(f"word '{frag}' (#{n}) not in scene {self.sc['id']}")
    def smooth(self, key, target, t, speed=4.0):
        v, lt = self._sm.get(key, (target, t))
        a = 1 - math.exp(-max(0, t - lt) * speed); v = v + (target - v) * a
        self._sm[key] = (v, t); return v
    def sfx(self, name, at, vol=1.0):
        """Schedule a sound effect at local time `at` (seconds from scene start)."""
        self._cues[(name, round(self.t0 + at, 2))] = vol

def endcard(c, t, s, cfg, part):
    lab, title = cfg.get("parts", {}).get(str(part), {}).get("end", [tr("конец", "the end"), cfg.get("title", "")])
    light = captions.CAP.get("spoken", "#ffffff") != "#ffffff"
    if light:
        src(c, "#f4efe4"); c.paint(); fg, fg2 = "#1b1b1f", "#555555"
    else:
        sky(c, t, 0.0); world.fog(c, t, 0.15, 600, 900); darken(c, 0.35); fg, fg2 = "#ffffff", "#dddddd"
    a = seg(t, 0.2, 0.8)
    text(c, lab, W / 2, 560, 24, fg2, a=a)
    sz = 60 if text_w(c, title, 60) < W - 60 else int(60 * (W - 60) / text_w(c, title, 60))
    text(c, title, W / 2, 628, sz, fg, a=a)
    if lab.lower() not in ("конец", "the end", "end"):
        text(c, cfg.get("next_label", tr("ПРОДОЛЖЕНИЕ СЛЕДУЕТ", "TO BE CONTINUED")), W / 2, 672, 16, C["red"], font=XB, a=a, track=2)

def overlay(c, t, kind):
    if kind == "rain": world.rain(c, t, 0.22)
    elif kind == "notebook":
        src(c, "#7fb0e0", 0.22); c.set_line_width(1.5)
        for y in range(120, H, 38): c.move_to(0, y); c.line_to(W, y)
        c.stroke(); src(c, "#ee8888", 0.35); c.set_line_width(2); c.move_to(60, 0); c.line_to(60, H); c.stroke()
    elif kind == "cork":
        src(c, "#9a7448"); c.set_line_width(26); c.rectangle(0, 0, W, H); c.stroke()

def make_frame(cfg, st, part, scenes_mod):
    stl = st["style"]; cap = st["cap"]
    step = engine.STYLE.get("step", 1); wob = engine.STYLE.get("wobble", 0.0)
    def frame(c, sc, s, t, T, allc, fi):
        c.set_source_rgb(0.03, 0.04, 0.07); c.paint()
        tq = math.floor(t * FPS / step) * step / FPS if step > 1 else t
        c.save()
        k = 1 + 0.035 * clamp(tq / max(s.dur, 0.1))
        c.translate(W / 2, 470); c.scale(k, k); c.translate(-W / 2, -470)
        if wob:
            r = random.Random(int(tq * FPS / max(step, 1)))
            c.translate(r.uniform(-wob, wob), r.uniform(-wob, wob)); c.rotate(r.uniform(-wob, wob) * 0.0015)
        fn = getattr(scenes_mod, "SCENES", {}).get(sc["id"])
        if fn is None and sc["id"] == "end": endcard(c, tq, s, cfg, part)
        elif fn is None: raise KeyError(f"no scene function for '{sc['id']}' in scenes_p{part}.py")
        else: fn(c, tq, s)
        c.restore()
        no_ov = getattr(scenes_mod, "NO_OVERLAY", ())   # scene ids without the style overlay (e.g. no rain indoors)
        if stl.get("overlay") and sc["id"] not in no_ov: overlay(c, t, stl["overlay"])
        if stl["post"] or stl["vignette"]:
            c.get_target().flush()
            arr = np.ndarray((H, W, 4), np.uint8, buffer=c.get_target().get_data())
            styles.post_process(arr, t, fi, stl)
            c.get_target().mark_dirty()
        g = cairo.LinearGradient(0, 800, 0, 1000)
        g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.45 if cap["spoken"] == "#ffffff" else 0.0)
        c.set_source(g); c.rectangle(0, 800, W, H - 800); c.fill()
        fa = 1 - seg(t, 0, 0.12)
        if fa > 0:
            # light styles (dark captions) dip to paper white instead of black, so cuts don't flash dark
            if captions.CAP.get("spoken", "#ffffff") != "#ffffff": c.set_source_rgba(0.97, 0.95, 0.91, fa * 0.9)
            else: c.set_source_rgba(0.02, 0.03, 0.06, fa * 0.9)
            c.paint()
        captions.draw_captions(c, T, allc, cap)
        if cfg.get("handle"): text(c, cfg["handle"], W - 24, H - 40, 15, "#ffffff", font=XB, anchor="r", a=0.45)
    return frame

def render_part(proj, part, only=None, stills=None, style_override=None):
    cfg, st, script = load_project(proj, style_override)
    tm = json.load(open(os.path.join(proj, "timing", f"p{part}.json"), encoding="utf-8"))
    allc = captions.build_chunks(tm)
    mod = load_scenes(proj, part)
    frame = make_frame(cfg, st, part, mod)
    odir = os.path.join(proj, "out", f"p{part}"); os.makedirs(odir, exist_ok=True)
    sdir = os.path.join(proj, "out", "stills"); os.makedirs(sdir, exist_ok=True)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cues = {}
    files = []
    for i, sc in enumerate(tm["scenes"]):
        s = S(sc, cues)
        f0 = round(sc["start"] * FPS) if i else 0; f1 = round(sc["end"] * FPS)
        if stills is not None:
            for (sid, frac) in stills:
                if sid == sc["id"]:
                    t = s.dur * frac; c = cairo.Context(surf); frame(c, sc, s, t, sc["start"] + t, allc, int((sc["start"] + t) * FPS))
                    tag = (style_override or cfg.get("style", "x"))
                    surf.write_to_png(os.path.join(sdir, f"p{part}_{sid}_{int(frac * 100)}_{tag}.png"))
            continue
        out = os.path.join(odir, f"{i:02d}_{sc['id']}.mp4"); files.append(out)
        if only and sc["id"] not in only and os.path.exists(out):
            # still need its sfx cues: run the scene cheaply at a few times
            for fi in range(f0, f1, 3):
                c = cairo.Context(surf)
                try: frame(c, sc, s, fi / FPS - sc["start"], fi / FPS, allc, fi)
                except Exception: pass
            continue
        tmp = out[:-4] + ".tmp.mp4"
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            T = fi / FPS; t = T - sc["start"]
            c = cairo.Context(surf); frame(c, sc, s, t, T, allc, fi)
            surf.flush(); p.stdin.write(surf.get_data())
        p.stdin.close(); assert p.wait() == 0
        os.replace(tmp, out); print("done", out, flush=True)
    if stills is not None: return None
    with open(os.path.join(odir, "list.txt"), "w") as f:
        for x in files: f.write(f"file '{os.path.basename(x)}'\n")
    video = os.path.join(proj, "out", f"video_p{part}.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(odir, "list.txt"), "-c", "copy", video], check=True)
    json.dump([{"name": k[0], "t": k[1], "vol": v} for k, v in sorted(cues.items(), key=lambda kv: kv[0][1])],
              open(os.path.join(proj, "out", f"sfx_p{part}.json"), "w"), indent=1)
    return video

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("proj"); ap.add_argument("part", type=int)
    ap.add_argument("--only", nargs="*"); ap.add_argument("--stills", nargs="*"); ap.add_argument("--style")
    a = ap.parse_args()
    if a.stills is not None:
        render_part(a.proj, a.part, stills=[(x.split(":")[0], float(x.split(":")[1])) for x in a.stills], style_override=a.style)
    else:
        print(render_part(a.proj, a.part, only=set(a.only) if a.only else None, style_override=a.style))
