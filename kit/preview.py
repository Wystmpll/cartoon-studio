"""Checkpoint previews.

  python preview.py chars PROJ [name ...]                 -> PROJ/out/charsheet.png (cast lineup in the project style)
  python preview.py styles PROJ PART SCENE FRAC [style ...] -> PROJ/out/styles_SCENE.jpg (same frame in many styles)
  python preview.py frames PROJ PART id:frac id:frac ...  -> PROJ/out/frames_pN.jpg (style frames / storyboard)
  python preview.py sheet OUT.jpg img1.png img2.png ...   -> contact sheet
"""
import sys, os, glob, subprocess, json
KIT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, KIT)
from PIL import Image, ImageDraw, ImageFont

def sheet(out, files, cols=4, w=270, labels=None):
    ims = [Image.open(f).convert("RGB").resize((w, int(w * 16 / 9))) for f in files]
    rows = (len(ims) + cols - 1) // cols; hh = int(w * 16 / 9) + (34 if labels else 0)
    sh = Image.new("RGB", (w * cols, hh * rows), (10, 12, 18))
    dr = ImageDraw.Draw(sh)
    try: font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 18)
    except Exception: font = None
    for i, im in enumerate(ims):
        x, y = (i % cols) * w, (i // cols) * hh
        sh.paste(im, (x, y))
        if labels: dr.text((x + 8, y + hh - 28), labels[i], fill=(240, 240, 240), font=font)
    sh.save(out, quality=88); return out

def chars_sheet(proj, names=None):
    import cairo, render, chars
    from engine import W, H, text, room_bg
    cfg, st, script = render.load_project(proj)
    names = names or cfg.get("cast") or list(chars.P)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(surf)
    from engine import src, hexc
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, *hexc("#141b2e")[:3]); g.add_color_stop_rgb(1, *hexc("#0a0d16")[:3])
    c.set_source(g); c.paint()
    per_row = 5 if len(names) > 10 else 4 if len(names) > 6 else 3 if len(names) > 3 else max(1, len(names))
    rows = [names[i:i + per_row] for i in range(0, len(names), per_row)]
    rh = min(520, (H - 150) / max(1, len(rows)))
    for r, row in enumerate(rows):
        y = 120 + (r + 1) * rh - 20
        Hh = rh * 0.78
        # police-lineup height marks: 150-190 cm
        for cm in (150, 160, 170, 180, 190):
            yy = y - Hh * cm / 185
            src(c, "#ffffff", 0.08); c.rectangle(0, yy, W, 1.5); c.fill()
            text(c, str(cm), 8, yy - 4, 11, "#ffffff", anchor="l", a=0.3)
        src(c, "#000000", 0.35); c.rectangle(0, y, W, 6); c.fill()
        for i, n in enumerate(row):
            x = W * (i + 0.5) / len(row)
            chars.person(c, n, x, y, Hh, 0.3, tag=True, tagt=-1, mood=chars.P[n].get("mood", "n"))
    text(c, cfg.get("title", "КАСТ").upper(), W / 2, 70, 30, "#ffffff")
    out = os.path.join(proj, "out", "charsheet.png"); os.makedirs(os.path.dirname(out), exist_ok=True)
    surf.write_to_png(out); return out

def styles_grid(proj, part, scene, frac, keys=None):
    import styles
    keys = keys or styles.ORDER
    files = []
    for k in keys:
        subprocess.run([sys.executable, os.path.join(KIT, "render.py"), proj, str(part), "--stills", f"{scene}:{frac}", "--style", k], check=True)
        files.append(os.path.join(proj, "out", "stills", f"p{part}_{scene}_{int(float(frac) * 100)}_{k}.png"))
    labels = [f"{i + 1}. {styles.S[k]['ru']}" for i, k in enumerate(keys)]
    return sheet(os.path.join(proj, "out", f"styles_{scene}.jpg"), files, cols=6 if len(files) > 8 else 4, w=240, labels=labels)

def frames(proj, part, specs):
    subprocess.run([sys.executable, os.path.join(KIT, "render.py"), proj, str(part), "--stills"] + specs, check=True)
    cfg = json.load(open(os.path.join(proj, "project.json")))
    files = [os.path.join(proj, "out", "stills", f"p{part}_{s.split(':')[0]}_{int(float(s.split(':')[1]) * 100)}_{cfg.get('style')}.png") for s in specs]
    return sheet(os.path.join(proj, "out", f"frames_p{part}.jpg"), files, cols=min(4, len(files)), w=300)

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "chars": print(chars_sheet(sys.argv[2], sys.argv[3:] or None))
    elif cmd == "styles": print(styles_grid(sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5], sys.argv[6:] or None))
    elif cmd == "frames": print(frames(sys.argv[2], int(sys.argv[3]), sys.argv[4:]))
    elif cmd == "sheet": print(sheet(sys.argv[2], sys.argv[3:]))
