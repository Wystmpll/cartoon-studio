import math, random, cairo
from engine import src, fill_rr, rrect, text, text_w, pop, seg, eout, clamp, lerp, C, hexc, STYLE

# ------------------------------------------------------------------
# Character designs: every one has its own silhouette + palette
# ------------------------------------------------------------------
P = {}   # character registry: name -> spec (see references/characters.md)

def register(name, spec):
    d = dict(h=180, skin="#e9b98f", hair="short", hc="#1d1510", top="hoodie", tc="#4c8bf5", t2="#2f5fb0",
             pants="#2b3550", shoes="#f2f2f2", acc=[], bw=1.0)
    d.update(spec); d.setdefault("acc", []); P[name] = d
    return d

def load_library(path, only=None):
    import json
    data = json.load(open(path, encoding="utf-8"))
    for k, v in data.items():
        if only is None or k in only: register(k, v)
    return list(data)

def shade(col, k):
    r, g, b, a = hexc(col)
    return (r * k, g * k, b * k, a)

def _limb(c, x, y, ang, L, w, col, end=None, endr=0):
    c.save(); c.translate(x, y); c.rotate(ang)
    fill_rr(c, -w / 2, 0, w, L, w / 2, col)
    if end: src(c, end); c.arc(0, L, endr, 0, 2 * math.pi); c.fill()
    c.restore()

def _blink(t, name):
    k = (t + (hash(name) % 37) * 0.13) % 3.7
    return 0.1 if k < 0.12 else 1.0

def person(c, name, x, y, H, t=0.0, look=0.0, mood="n", mouth=None, walk=None, run=False, arms=None,
           alpha=1.0, shake=0.0, sil=False, tag=False, tagt=-9, bob=True, lean=0.0, holding=None, eyes_closed=False,
           cover_mouth=False, glow_face=0.0, zombie=False):
    """x,y feet; H = height px of a 185cm person. mood: n, happy, scared, angry, sad, smug, focus.
    arms: (back_angle, front_angle) radians, 0 = hanging down, positive = forward/up."""
    d = P[name]
    Hp = H * d["h"] / 185
    R = 0.135 * Hp * STYLE.get("head_scale", 1.0)
    leg = 0.36 * Hp; torso = 0.29 * Hp
    bw = 0.25 * Hp * d.get("bw", 1.0) * (0.92 if d.get("girl") else 1.0)
    rng = random.Random(int(t * 30) * 7 + hash(name) % 97)
    sx = rng.uniform(-1, 1) * shake * 0.012 * Hp
    ph = walk if walk is not None else 0.0
    amp = 0.55 if run else 0.32
    bounce = abs(math.sin(ph * 2 * math.pi)) * (0.035 if run else 0.018) * Hp if walk is not None else 0.0
    breathe = math.sin(t * 2.1 + hash(name) % 10) * 0.006 * Hp if bob else 0
    c.save(); c.translate(x + sx, y)
    # shadow
    src(c, "#000000", 0.28 * alpha); c.save(); c.scale(1, 0.22); c.arc(0, 0, bw * 0.75, 0, 2 * math.pi); c.restore(); c.fill()
    c.push_group()
    c.translate(0, -bounce)
    c.rotate(lean + (0.12 if run else 0))
    skin = "#0b0e16" if sil else ("#9aab8e" if zombie else d["skin"])
    tc = "#0b0e16" if sil else d["tc"]; t2 = "#0b0e16" if sil else d["t2"]
    pants = "#0b0e16" if sil else d["pants"]; shoes = "#0b0e16" if sil else d["shoes"]
    hc = "#0b0e16" if sil else d["hc"]
    hipy = -leg
    # legs
    for i, sgn in enumerate((-1, 1)):
        a = math.sin(ph * 2 * math.pi + i * math.pi) * amp if walk is not None else 0
        c.save(); c.translate(sgn * bw * 0.2, hipy); c.rotate(a)
        lw = bw * 0.3
        if d["top"] == "crop" and not sil:
            fill_rr(c, -lw / 2, 0, lw, leg * 0.96, lw * 0.45, pants)
        else:
            fill_rr(c, -lw / 2, 0, lw, leg * 0.96, lw * 0.3, pants if i else shade(pants, 0.85) if not sil else pants)
        fill_rr(c, -lw * 0.6, leg * 0.9, lw * 1.45, lw * 0.5, lw * 0.25, shoes)
        if d["top"] == "track" and not sil:
            src(c, d["t2"]); c.rectangle(lw * 0.3, 2, lw * 0.15, leg * 0.85); c.fill()
        if d["top"] == "pj" and not sil:
            src(c, d["t2"], 0.8)
            for k in range(4): c.rectangle(-lw / 2, leg * (0.1 + k * 0.2), lw, leg * 0.05); c.fill()
        c.restore()
    # arms helper
    def arm(sgn, ang):
        c.save(); c.translate(sgn * bw * 0.46, -leg - torso * 0.92)
        sw = -math.sin(ph * 2 * math.pi + (0 if sgn > 0 else math.pi)) * amp * 1.1 if walk is not None else 0
        c.rotate(sgn * 0.06 + sw - ang * (1 if sgn > 0 else 1))
        aw = bw * 0.24; L = torso * 0.98
        col = tc if d["top"] not in ("tee", "jersey", "crop") else skin
        sleeve = tc
        if d["top"] in ("tee", "jersey"):
            fill_rr(c, -aw / 2, 0, aw, L, aw / 2, skin); fill_rr(c, -aw * 0.6, -aw * 0.2, aw * 1.2, L * 0.38, aw * 0.4, sleeve)
        elif d["top"] == "crop":
            fill_rr(c, -aw / 2, 0, aw, L, aw / 2, tc)
        else:
            fill_rr(c, -aw / 2, 0, aw, L, aw / 2, shade(tc, 0.9) if not sil else tc)
            if d["top"] == "track" and not sil:
                src(c, d["t2"]); c.rectangle(-aw * 0.1, 0, aw * 0.2, L * 0.9); c.fill()
        if "sleeve" in d["acc"] and sgn > 0 and not sil:
            fill_rr(c, -aw * 0.6, L * 0.55, aw * 1.2, L * 0.25, aw * 0.2, "#e9e4d8")
            src(c, "#7a1f2b", 0.85); c.arc(aw * 0.1, L * 0.66, aw * 0.25, 0, 2 * math.pi); c.fill()
        src(c, skin); c.arc(0, L, aw * 0.55, 0, 2 * math.pi); c.fill()
        if sgn > 0 and holding and not sil:
            hold_item(c, holding, 0, L, aw, t)
        if sgn > 0 and "thread" in d["acc"] and not sil:
            fill_rr(c, -aw * 0.58, L * 0.84, aw * 1.16, aw * 0.16, 1, "#e5484d")
        if sgn > 0 and "bandage" in d["acc"] and not sil:
            fill_rr(c, -aw * 0.6, L * 0.78, aw * 1.2, aw * 0.6, 3, "#f2efe6"); src(c, "#b33a3a", 0.8); c.arc(aw * 0.1, L * 0.9, aw * 0.15, 0, 2 * math.pi); c.fill()
        if sgn > 0 and "watch" in d["acc"] and not sil:
            fill_rr(c, -aw * 0.6, L * 0.82, aw * 1.2, aw * 0.4, 2, "#d9d9d9")
        c.restore()
    ab, af = arms if arms else (0.0, 0.0)
    arm(-1, ab)
    # torso
    ty = -leg - torso
    top = d["top"]
    if top == "crop":
        fill_rr(c, -bw / 2, ty, bw, torso * 0.62, bw * 0.3, tc)
        fill_rr(c, -bw * 0.42, ty + torso * 0.55, bw * 0.84, torso * 0.5, bw * 0.15, "#2e2a40" if not sil else tc)
        src(c, t2); c.rectangle(-bw * 0.42, ty + torso * 0.55, bw * 0.84, torso * 0.06); c.fill()
    else:
        fill_rr(c, -bw / 2, ty, bw, torso + bw * 0.12, bw * 0.3, tc)
        if not sil:
            src(c, "#000000", 0.12); c.rectangle(bw * 0.18, ty + bw * 0.1, bw * 0.3, torso); c.fill()
    if not sil:
        if top in ("hoodie", "hoodup"):
            fill_rr(c, -bw * 0.28, ty + torso * 0.55, bw * 0.56, torso * 0.28, bw * 0.08, shade(tc, 0.85))
            src(c, "#f2f2f2"); c.set_line_width(max(1, bw * 0.03))
            c.move_to(-bw * 0.08, ty + 2); c.line_to(-bw * 0.1, ty + torso * 0.3); c.move_to(bw * 0.08, ty + 2); c.line_to(bw * 0.1, ty + torso * 0.3); c.stroke()
        if top == "jacket":
            src(c, t2); c.move_to(-bw * 0.16, ty); c.line_to(bw * 0.16, ty); c.line_to(bw * 0.12, ty + torso + bw * 0.1); c.line_to(-bw * 0.12, ty + torso + bw * 0.1); c.close_path(); c.fill()
            src(c, shade(tc, 0.75)); c.set_line_width(bw * 0.03); c.move_to(-bw * 0.16, ty); c.line_to(-bw * 0.12, ty + torso); c.move_to(bw * 0.16, ty); c.line_to(bw * 0.12, ty + torso); c.stroke()
        if top == "coat":
            src(c, t2); c.move_to(0, ty); c.line_to(bw * 0.12, ty + torso + bw * 0.12); c.line_to(-bw * 0.12, ty + torso + bw * 0.12); c.close_path(); c.fill()
            fill_rr(c, -bw / 2, ty + torso * 0.9, bw, torso * 0.35, bw * 0.15, tc)
            src(c, "#d9c27a"); [c.arc(-bw * 0.2, ty + torso * (0.35 + k * 0.22), bw * 0.035, 0, 2 * math.pi) or c.fill() for k in range(3)]
        if top == "shirt":
            src(c, t2); c.move_to(-bw * 0.14, ty); c.line_to(0, ty + torso * 0.2); c.line_to(bw * 0.14, ty); c.close_path(); c.fill()
            src(c, shade(tc, 0.75)); c.set_line_width(bw * 0.025); c.move_to(0, ty + torso * 0.2); c.line_to(0, ty + torso); c.stroke()
        if top == "tee":
            if name == "Чина":
                text(c, "LOUD", 0, ty + torso * 0.6, bw * 0.24, "#1b1b1f")
        if top == "track":
            src(c, t2); c.rectangle(-bw * 0.04, ty, bw * 0.08, torso); c.fill()
            c.rectangle(-bw / 2, ty + torso * 0.15, bw, bw * 0.05); c.fill()
        if top == "blazer":
            src(c, t2); c.move_to(-bw * 0.15, ty); c.line_to(bw * 0.15, ty); c.line_to(0, ty + torso * 0.6); c.close_path(); c.fill()
            src(c, "#7a1f2b"); c.move_to(-bw * 0.04, ty + 3); c.line_to(bw * 0.04, ty + 3); c.line_to(bw * 0.05, ty + torso * 0.5); c.line_to(0, ty + torso * 0.58); c.line_to(-bw * 0.05, ty + torso * 0.5); c.close_path(); c.fill()
            src(c, "#f5c542"); c.rectangle(bw * 0.22, ty + torso * 0.3, bw * 0.12, bw * 0.04); c.fill()
        if top == "jersey":
            text(c, "23", 0, ty + torso * 0.62, bw * 0.38, t2)
            src(c, t2); c.rectangle(-bw / 2, ty + torso * 0.05, bw, bw * 0.04); c.fill()
        if top == "cardi":
            src(c, t2); c.move_to(-bw * 0.13, ty); c.line_to(bw * 0.13, ty); c.line_to(bw * 0.08, ty + torso + bw * 0.1); c.line_to(-bw * 0.08, ty + torso + bw * 0.1); c.close_path(); c.fill()
            src(c, shade(tc, 0.7))
            for k in range(3): c.arc(-bw * 0.17, ty + torso * (0.25 + k * 0.25), bw * 0.03, 0, 2 * math.pi); c.fill()
        if top == "pj":
            src(c, t2, 0.8)
            for k in range(4): c.rectangle(-bw / 2 + 2, ty + torso * (0.15 + k * 0.22), bw - 4, torso * 0.07); c.fill()
        if "mono" in d["acc"]:
            src(c, "#d9b45a", 0.9)
            for k in range(5):
                for j in range(2):
                    xx = (-0.4 if j == 0 else 0.28) * bw; yy = ty + torso * (0.12 + k * 0.18)
                    c.arc(xx + (k % 2) * bw * 0.06, yy, bw * 0.022, 0, 2 * math.pi); c.fill()
        if "chain" in d["acc"]:
            src(c, "#f5c542"); c.set_line_width(bw * 0.035); c.arc(0, ty + torso * 0.05, bw * 0.2, 0.15 * math.pi, 0.85 * math.pi); c.stroke()
        if "scarf" in d["acc"]:
            fill_rr(c, -bw * 0.35, ty - bw * 0.06, bw * 0.7, bw * 0.18, bw * 0.08, "#8f2d3b")
            fill_rr(c, bw * 0.05, ty, bw * 0.13, torso * 0.45, bw * 0.05, "#8f2d3b")
    # neck & head
    hy = ty - R * 0.92 + breathe
    src(c, skin); c.rectangle(-R * 0.25, hy + R * 0.6, R * 0.5, R * 0.5); c.fill()
    if top == "hoodie" and not sil:
        fill_rr(c, -bw * 0.38, ty - bw * 0.08, bw * 0.76, bw * 0.2, bw * 0.1, shade(tc, 0.8))
    dh = dict(d); dh["skin"] = skin
    draw_head(c, name, dh, 0, hy, R, t, look, mood, mouth, sil, eyes_closed, zombie)
    if cover_mouth and not sil:
        fill_rr(c, -R * 0.45, hy + R * 0.25, R * 0.9, R * 0.45, R * 0.2, shade(d["skin"], 0.92))
    arm(1, af)
    _finish(c, alpha, Hp)
    c.restore()
    if glow_face > 0:
        from engine import glow
        glow(c, x, y - Hp * 0.8, R * 3, (1, 0.95, 0.7), 0.25 * glow_face)
    if tag:
        k = pop(t, tagt, 0.3)
        if k > 0:
            sz = max(15, min(24, int(Hp * 0.075)))
            w = text_w(c, name.upper(), sz) + 22; hh = sz + 12
            side = Hp > 480
            if side:
                hyy = y - (0.36 + 0.29) * Hp - R * 0.92
                tx = x + R * 1.35 + w / 2
                if tx + w / 2 > 712: tx = x - R * 1.35 - w / 2
                c.save(); c.translate(tx, hyy - R * 0.6); c.scale(k, k)
            else:
                c.save(); c.translate(x, y - Hp - R * 0.9 - 18); c.scale(k, k)
            fill_rr(c, -w / 2, -hh / 2, w, hh, 6, d["tc"])
            fg = "#111111" if name in ("Санжар", "Сула", "Чина", "Камила", "Айдана", "Нурали") else "#ffffff"
            text(c, name.upper(), 0, sz * 0.36, sz, fg)
            if not side: src(c, d["tc"]); c.move_to(-6, hh / 2 - 1); c.line_to(6, hh / 2 - 1); c.line_to(0, hh / 2 + 6); c.close_path(); c.fill()
            c.restore()
    return Hp


def _finish(c, alpha, Hp):
    """Composite the character group with style treatments (outline, drop shadow, cel/clay shading, neon)."""
    pat = c.pop_group()
    st = STYLE
    ow = st.get("outline", 0.0) * Hp / 260.0
    if st.get("drop_shadow", 0) > 0:
        d = st["drop_shadow"] * Hp / 260.0
        c.save(); c.translate(d, d * 0.8); c.set_source_rgba(0, 0, 0, 0.35 * alpha); c.mask(pat); c.restore()
    if ow > 0.3:
        col = hexc(st.get("neon") or st.get("outline_col", "#111111"))
        steps = 8 if ow < 4 else 12
        for i in range(steps):
            a = 2 * math.pi * i / steps
            c.save(); c.translate(math.cos(a) * ow, math.sin(a) * ow); c.set_source_rgba(col[0], col[1], col[2], alpha); c.mask(pat); c.restore()
    if st.get("neon"):
        c.save(); c.set_source(pat); c.paint_with_alpha(alpha); c.restore()
        c.save(); c.set_source_rgba(0.02, 0.02, 0.08, 0.55 * alpha); c.mask(pat); c.restore()
        return
    c.set_source(pat); c.paint_with_alpha(alpha)
    if st.get("cel", 0) > 0:
        c.save(); c.rectangle(Hp * 0.02, -Hp * 1.6, Hp, Hp * 1.8); c.clip()
        c.set_source_rgba(0.05, 0.02, 0.15, 0.22 * st["cel"] * alpha); c.mask(pat); c.restore()
    if st.get("clay", 0) > 0:
        g = cairo.RadialGradient(-Hp * 0.12, -Hp * 0.95, Hp * 0.02, -Hp * 0.05, -Hp * 0.7, Hp * 0.9)
        g.add_color_stop_rgba(0, 1, 1, 1, 0.35 * st["clay"]); g.add_color_stop_rgba(0.35, 1, 1, 1, 0.0)
        g.add_color_stop_rgba(0.8, 0, 0, 0, 0.0); g.add_color_stop_rgba(1, 0, 0, 0, 0.3 * st["clay"])
        c.save(); c.set_source(g); c.mask(pat); c.restore()

def hold_item(c, item, x, y, aw, t):
    c.save(); c.translate(x, y)
    if item == "flashlight":
        fill_rr(c, -aw * 0.35, -aw * 0.2, aw * 0.7, aw * 2.0, aw * 0.15, "#3b4252"); fill_rr(c, -aw * 0.5, aw * 1.6, aw, aw * 0.5, aw * 0.15, "#f5c542")
    elif item == "phone":
        fill_rr(c, -aw * 0.5, -aw * 0.4, aw, aw * 1.7, aw * 0.18, "#1b1b1f"); fill_rr(c, -aw * 0.38, -aw * 0.28, aw * 0.76, aw * 1.4, aw * 0.1, "#7cc7ff")
    elif item == "radio":
        fill_rr(c, -aw * 0.7, -aw * 0.3, aw * 1.4, aw * 2.0, aw * 0.2, "#2a2f3a"); src(c, "#555c6e"); c.set_line_width(aw * 0.15); c.move_to(aw * 0.4, -aw * 0.3); c.line_to(aw * 0.6, -aw * 1.8); c.stroke()
        src(c, C["grn"]); c.arc(0, aw * 0.6, aw * 0.18, 0, 2 * math.pi); c.fill()
    c.restore()

def draw_head(c, name, d, x, hy, R, t, look, mood, mouth, sil, eyes_closed, zombie):
    skin = "#0b0e16" if sil else d["skin"]; hc = "#0b0e16" if sil else d["hc"]
    hs = d["hair"]
    # back hair
    src(c, hc)
    if hs == "long":
        fill_rr(c, x - R * 1.15, hy - R * 0.9, R * 2.3, R * 2.6, R * 0.9, hc)
    if hs == "volume":
        for ox, oy, rr in ((-1.0, 0.2, 0.7), (1.0, 0.2, 0.7), (-0.85, 0.85, 0.6), (0.85, 0.85, 0.6), (0, -0.6, 0.9)):
            src(c, hc); c.arc(x + ox * R, hy + oy * R, rr * R, 0, 2 * math.pi); c.fill()
    if d["top"] == "hoodup":
        src(c, "#0b0e16" if sil else d["t2"]); c.arc(x, hy + R * 0.05, R * 1.3, 0, 2 * math.pi); c.fill()
    # ears
    src(c, skin); c.arc(x - R * 0.98, hy + R * 0.1, R * 0.2, 0, 2 * math.pi); c.fill(); c.arc(x + R * 0.98, hy + R * 0.1, R * 0.2, 0, 2 * math.pi); c.fill()
    # face
    src(c, skin); c.save(); c.translate(x, hy); c.scale(1.0, 1.04); c.arc(0, 0, R, 0, 2 * math.pi); c.restore(); c.fill()
    if not sil and not zombie:
        src(c, "#ff7a7a", 0.18); c.arc(x - R * 0.55, hy + R * 0.3, R * 0.18, 0, 2 * math.pi); c.fill(); c.arc(x + R * 0.55, hy + R * 0.3, R * 0.18, 0, 2 * math.pi); c.fill()
    # front hair
    src(c, hc)
    if hs == "curly":
        rng = random.Random(5)
        for i in range(13):
            a = math.pi * (1.0 + i / 12)
            c.arc(x + math.cos(a) * R * 0.95, hy - R * 0.1 + math.sin(a) * R * 0.95, R * 0.34, 0, 2 * math.pi); c.fill()
        for ox in (-0.5, 0, 0.5): c.arc(x + ox * R, hy - R * 0.85, R * 0.42, 0, 2 * math.pi); c.fill()
        for ox in (-0.35, 0.15): c.arc(x + ox * R, hy - R * 0.55, R * 0.25, 0, 2 * math.pi); c.fill()
    elif hs == "slick":
        c.arc(x, hy - R * 0.1, R * 1.03, math.pi * 1.02, math.pi * 1.98); c.close_path(); c.fill()
        c.move_to(x - R, hy - R * 0.2); c.curve_to(x - R * 0.2, hy - R * 0.9, x + R * 0.6, hy - R * 0.5, x + R * 1.02, hy - R * 0.15); c.line_to(x + R, hy - R * 0.5); c.close_path(); c.fill()
    elif hs == "quiff":
        c.arc(x, hy - R * 0.15, R * 1.0, math.pi, 2 * math.pi); c.close_path(); c.fill()
        c.move_to(x - R * 0.6, hy - R * 0.8); c.curve_to(x - R * 0.2, hy - R * 1.9, x + R * 1.2, hy - R * 1.6, x + R * 0.9, hy - R * 0.6); c.close_path(); c.fill()
    elif hs == "messy":
        c.arc(x, hy - R * 0.12, R * 1.02, math.pi, 2 * math.pi); c.close_path(); c.fill()
        for i in range(7):
            a = math.pi * (1.1 + i * 0.13)
            c.move_to(x + math.cos(a) * R * 0.8, hy - R * 0.1 + math.sin(a) * R * 0.8); c.line_to(x + math.cos(a + 0.12) * R * 1.35, hy + math.sin(a + 0.12) * R * 1.35); c.line_to(x + math.cos(a + 0.25) * R * 0.8, hy - R * 0.1 + math.sin(a + 0.25) * R * 0.8); c.close_path(); c.fill()
    elif hs == "curtain":
        c.arc(x, hy - R * 0.2, R * 1.04, math.pi, 2 * math.pi); c.close_path(); c.fill()
        for sgn in (-1, 1):
            c.move_to(x, hy - R * 0.95); c.curve_to(x + sgn * R * 0.35, hy - R * 0.6, x + sgn * R * 0.7, hy - R * 0.35, x + sgn * R * 1.02, hy + R * 0.05)
            c.line_to(x + sgn * R * 1.06, hy - R * 0.4); c.curve_to(x + sgn * R * 0.8, hy - R * 0.95, x + sgn * R * 0.3, hy - R * 1.12, x, hy - R * 1.05); c.close_path(); c.fill()
    elif hs == "short":
        c.arc(x, hy - R * 0.2, R * 1.0, math.pi * 1.0, math.pi * 2.0); c.close_path(); c.fill()
    elif hs == "wavy":
        c.arc(x, hy - R * 0.15, R * 1.03, math.pi, 2 * math.pi); c.close_path(); c.fill()
        for i in range(5): c.arc(x - R * 0.8 + i * R * 0.4, hy - R * 0.25, R * 0.24, 0, math.pi); c.fill()
    elif hs == "bangs":
        c.arc(x, hy - R * 0.1, R * 1.05, math.pi * 0.95, math.pi * 2.05); c.close_path(); c.fill()
        c.rectangle(x - R * 0.95, hy - R * 0.35, R * 1.9, R * 0.32); c.fill()
    elif hs == "buzz":
        src(c, hc, 0.85 if not sil else 1); c.arc(x, hy - R * 0.25, R * 0.98, math.pi * 1.05, math.pi * 1.95); c.close_path(); c.fill()
    elif hs == "side":
        c.arc(x, hy - R * 0.15, R * 1.03, math.pi, 2 * math.pi); c.close_path(); c.fill()
        c.move_to(x - R * 0.2, hy - R * 1.05); c.curve_to(x + R * 0.5, hy - R * 0.9, x + R * 0.9, hy - R * 0.6, x + R * 1.05, hy - R * 0.2); c.line_to(x + R * 1.05, hy - R * 0.6); c.close_path(); c.fill()
        src(c, "#000000" if sil else "#ffffff", 0.0)
    elif hs == "cap":
        src(c, "#0b0e16" if sil else "#2d6cdf"); c.arc(x, hy - R * 0.2, R * 1.05, math.pi, 2 * math.pi); c.close_path(); c.fill()
        c.save(); c.translate(x, hy - R * 0.25); c.rotate(-0.08); fill_rr(c, -R * 0.2, -R * 0.12, R * 1.7, R * 0.24, R * 0.1, "#0b0e16" if sil else "#1f4fb0"); c.restore()
        if not sil: src(c, "#ffffff"); c.arc(x - R * 0.1, hy - R * 0.75, R * 0.14, 0, 2 * math.pi); c.fill()
    elif hs == "volume":
        c.arc(x, hy - R * 0.25, R * 1.05, math.pi * 1.0, math.pi * 2.0); c.close_path(); c.fill()
        c.move_to(x - R * 1.05, hy - R * 0.25); c.curve_to(x - R * 0.4, hy - R * 0.2, x + R * 0.1, hy - R * 0.5, x + R * 0.3, hy - R * 0.9); c.line_to(x - R * 0.6, hy - R * 0.9); c.close_path(); c.fill()
    elif hs == "bun":
        c.arc(x, hy - R * 0.2, R * 1.02, math.pi, 2 * math.pi); c.close_path(); c.fill()
        c.arc(x, hy - R * 1.25, R * 0.45, 0, 2 * math.pi); c.fill()
        if not sil: src(c, d["tc"]); c.rectangle(x - R * 0.35, hy - R * 0.98, R * 0.7, R * 0.12); c.fill()
    elif hs == "long":
        c.arc(x, hy - R * 0.2, R * 1.04, math.pi * 1.0, math.pi * 2.0); c.close_path(); c.fill()
        c.move_to(x - R * 1.04, hy - R * 0.2); c.curve_to(x - R * 0.3, hy - R * 0.1, x + R * 0.2, hy - R * 0.4, x + R * 0.4, hy - R * 0.9); c.close_path(); c.fill()
    elif hs == "fade":
        c.arc(x, hy - R * 0.25, R * 1.0, math.pi * 1.03, math.pi * 1.97); c.close_path(); c.fill()
        src(c, hc, 0.4); c.arc(x, hy - R * 0.15, R * 1.02, math.pi * 0.95, math.pi * 2.05); c.close_path(); c.fill()
    if sil: return
    # face features
    ex = R * 0.36; ey = hy + R * 0.08; lx = look * R * 0.12
    blink = 0.08 if eyes_closed else _blink(t, name)
    if zombie:
        src(c, "#f2f2e8")
        for sgn in (-1, 1): c.save(); c.translate(x + sgn * ex, ey); c.scale(1, 0.85); c.arc(0, 0, R * 0.2, 0, 2 * math.pi); c.restore(); c.fill()
    elif STYLE.get("eye") == "anime":
        iris = d.get("eye", "#5a3a22")
        for sgn in (-1, 1):
            c.save(); c.translate(x + sgn * ex, ey); c.scale(1, blink)
            src(c, "#ffffff"); c.save(); c.scale(0.9, 1.25); c.arc(0, 0, R * 0.24, 0, 2 * math.pi); c.restore(); c.fill()
            src(c, iris); c.save(); c.scale(0.8, 1.2); c.arc(lx, R * 0.03, R * 0.19, 0, 2 * math.pi); c.restore(); c.fill()
            src(c, "#120c0c"); c.save(); c.scale(0.8, 1.2); c.arc(lx, R * 0.05, R * 0.1, 0, 2 * math.pi); c.restore(); c.fill()
            src(c, "#ffffff"); c.arc(lx + R * 0.06, -R * 0.08, R * 0.07, 0, 2 * math.pi); c.fill(); c.arc(lx - R * 0.06, R * 0.12, R * 0.035, 0, 2 * math.pi); c.fill()
            src(c, "#120c0c"); c.set_line_width(R * 0.07); c.arc(0, 0, R * 0.25, math.pi * 1.1, math.pi * 1.9); c.stroke()
            c.restore()
    elif STYLE.get("eye") == "pie":
        for sgn in (-1, 1):
            c.save(); c.translate(x + sgn * ex, ey); c.scale(1, blink)
            src(c, "#ffffff"); c.save(); c.scale(0.8, 1.3); c.arc(0, 0, R * 0.22, 0, 2 * math.pi); c.restore(); c.fill()
            src(c, "#0a0a0a"); c.save(); c.scale(0.6, 1.15); c.arc(lx, R * 0.04, R * 0.2, 0, 2 * math.pi); c.restore(); c.fill()
            src(c, "#ffffff"); c.move_to(lx, R * 0.04); c.arc(lx, R * 0.04, R * 0.2, -0.9, -0.4); c.close_path(); c.fill()
            c.restore()
    elif STYLE.get("eye") == "dot":
        for sgn in (-1, 1):
            c.save(); c.translate(x + sgn * ex, ey); c.scale(1, blink)
            src(c, "#141414"); c.arc(lx, 0, R * 0.09, 0, 2 * math.pi); c.fill(); c.restore()
    else:
        for sgn in (-1, 1):
            c.save(); c.translate(x + sgn * ex, ey); c.scale(1, blink)
            src(c, "#ffffff"); c.save(); c.scale(1, 1.15); c.arc(0, 0, R * 0.19, 0, 2 * math.pi); c.restore(); c.fill()
            psz = R * (0.15 if mood == "scared" else 0.12)
            src(c, "#1a1414"); c.arc(lx, R * 0.02, psz, 0, 2 * math.pi); c.fill()
            src(c, "#ffffff"); c.arc(lx + psz * 0.35, -psz * 0.35, psz * 0.3, 0, 2 * math.pi); c.fill()
            c.restore()
            if "lashes" in d["acc"] and blink > 0.5:
                src(c, "#1a1414"); c.set_line_width(R * 0.06)
                c.move_to(x + sgn * (ex + R * 0.18), ey - R * 0.1); c.line_to(x + sgn * (ex + R * 0.28), ey - R * 0.2); c.stroke()
    # brows
    src(c, d["hc"] if not zombie else "#3a3f36"); c.set_line_width(R * 0.09); c.set_line_cap(cairo.LINE_CAP_ROUND)
    by = ey - R * 0.33
    tilt = {"angry": 0.14, "scared": -0.12, "sad": -0.1, "smug": 0.05, "focus": 0.08}.get(mood, 0.0) * R
    rise = {"scared": -0.06, "happy": -0.04}.get(mood, 0) * R
    for sgn in (-1, 1):
        c.move_to(x + sgn * (ex - R * 0.16), by + rise + tilt); c.line_to(x + sgn * (ex + R * 0.16), by + rise - tilt * 0.3 - (R * 0.06 if (mood == "smug" and sgn > 0) else 0)); c.stroke()
    c.set_line_cap(cairo.LINE_CAP_BUTT)
    # glasses
    if "glasses" in d["acc"]:
        src(c, "#111111"); c.set_line_width(R * 0.06)
        for sgn in (-1, 1): rrect(c, x + sgn * ex - R * 0.26, ey - R * 0.22, R * 0.52, R * 0.42, R * 0.12); c.stroke()
        c.move_to(x - ex + R * 0.26, ey - R * 0.05); c.line_to(x + ex - R * 0.26, ey - R * 0.05); c.stroke()
    # beard
    if "beard" in d["acc"]:
        src(c, d["hc"], 0.85); c.move_to(x - R * 0.9, hy + R * 0.1); c.curve_to(x - R * 0.75, hy + R * 0.95, x + R * 0.75, hy + R * 0.95, x + R * 0.9, hy + R * 0.1)
        c.curve_to(x + R * 0.6, hy + R * 0.62, x - R * 0.6, hy + R * 0.62, x - R * 0.9, hy + R * 0.1); c.fill()
    # mouth
    m = mouth or {"happy": "smile", "scared": "o", "angry": "grit", "sad": "down", "smug": "smirk", "focus": "flat"}.get(mood, "n")
    if "grin" in d["acc"] and m == "n": m = "smile"
    my = hy + R * 0.52
    src(c, "#5a1d1d" if not zombie else "#2a1a1a"); c.set_line_width(R * 0.08)
    if zombie:
        c.save(); c.translate(x, my); c.scale(1.2, 0.8); c.arc(0, 0, R * 0.18, 0, 2 * math.pi); c.restore(); c.fill()
    elif m == "smile":
        c.move_to(x - R * 0.28, my - R * 0.05); c.curve_to(x - R * 0.1, my + R * 0.22, x + R * 0.1, my + R * 0.22, x + R * 0.28, my - R * 0.05); c.close_path(); c.fill()
    elif m == "laugh":
        c.move_to(x - R * 0.32, my - R * 0.08); c.curve_to(x - R * 0.15, my + R * 0.4, x + R * 0.15, my + R * 0.4, x + R * 0.32, my - R * 0.08); c.close_path(); c.fill()
        src(c, "#ffffff"); c.rectangle(x - R * 0.22, my - R * 0.07, R * 0.44, R * 0.07); c.fill()
    elif m == "o":
        c.save(); c.translate(x, my + R * 0.03); c.scale(0.8, 1); c.arc(0, 0, R * 0.13, 0, 2 * math.pi); c.restore(); c.fill()
    elif m == "shout":
        c.save(); c.translate(x, my + R * 0.05); c.scale(1.1, 1.0); c.arc(0, 0, R * 0.22, 0, 2 * math.pi); c.restore(); c.fill()
        src(c, "#e06b6b"); c.arc(x, my + R * 0.15, R * 0.1, 0, math.pi); c.fill()
    elif m == "grit":
        fill_rr(c, x - R * 0.25, my - R * 0.04, R * 0.5, R * 0.14, R * 0.04, "#ffffff")
        src(c, "#5a1d1d"); c.set_line_width(R * 0.04); rrect(c, x - R * 0.25, my - R * 0.04, R * 0.5, R * 0.14, R * 0.04); c.stroke()
    elif m == "down":
        c.arc(x, my + R * 0.14, R * 0.18, 1.15 * math.pi, 1.85 * math.pi); c.stroke()
    elif m == "smirk":
        c.move_to(x - R * 0.2, my + R * 0.02); c.curve_to(x, my + R * 0.08, x + R * 0.15, my + R * 0.02, x + R * 0.27, my - R * 0.1); c.stroke()
    elif m == "flat":
        c.move_to(x - R * 0.18, my); c.line_to(x + R * 0.18, my); c.stroke()
    elif m == "talk":
        k = abs(math.sin(t * 16))
        c.save(); c.translate(x, my + R * 0.02); c.scale(1, 0.3 + k * 0.9); c.arc(0, 0, R * 0.15, 0, 2 * math.pi); c.restore(); c.fill()
    else:
        c.move_to(x - R * 0.13, my); c.curve_to(x - R * 0.05, my + R * 0.05, x + R * 0.05, my + R * 0.05, x + R * 0.13, my); c.stroke()
    # accessories on head
    if "phones" in d["acc"]:
        src(c, "#1b1f2a"); c.set_line_width(R * 0.16); c.arc(x, hy - R * 0.1, R * 1.12, math.pi * 1.05, math.pi * 1.95); c.stroke()
        for sgn in (-1, 1): fill_rr(c, x + sgn * R * 1.08 - R * 0.2, hy - R * 0.25, R * 0.4, R * 0.6, R * 0.15, "#2fb47c" if sgn > 0 else "#1b1f2a")
    if "band" in d["acc"]:
        fill_rr(c, x - R * 1.02, hy - R * 0.55, R * 2.04, R * 0.2, R * 0.08, "#ffffff")
    if "shades" in d["acc"]:
        fill_rr(c, x - R * 0.75, hy - R * 0.95, R * 0.6, R * 0.28, R * 0.1, "#111111"); fill_rr(c, x + R * 0.15, hy - R * 0.95, R * 0.6, R * 0.28, R * 0.1, "#111111")
    if "sleepy" in d["acc"]:
        src(c, d["skin"])
        for sgn in (-1, 1): c.rectangle(x + sgn * R * 0.36 - R * 0.24, hy - R * 0.2, R * 0.48, R * 0.24); c.fill()
        src(c, "#1a1414"); c.set_line_width(R * 0.06)
        for sgn in (-1, 1): c.move_to(x + sgn * R * 0.36 - R * 0.2, hy + R * 0.04); c.line_to(x + sgn * R * 0.36 + R * 0.2, hy + R * 0.04); c.stroke()
    if "stink" in d["acc"]:
        src(c, "#9bd36a", 0.7); c.set_line_width(R * 0.07)
        for k in range(3):
            ox = x + (k - 1) * R * 0.7; base = hy - R * 1.4 - ((t * 20 + k * 7) % 12) * R * 0.03
            c.move_to(ox, base + R * 0.5)
            for j in range(4): c.curve_to(ox + R * 0.15, base + R * (0.4 - j * 0.15), ox - R * 0.15, base + R * (0.32 - j * 0.15), ox, base + R * (0.25 - j * 0.15))
            c.stroke()
    if "hoops" in d["acc"]:
        src(c, "#f5c542"); c.set_line_width(R * 0.06)
        for sgn in (-1, 1): c.arc(x + sgn * R * 1.0, hy + R * 0.42, R * 0.17, 0, 2 * math.pi); c.stroke()

# ------------------------------------------------------------------
ZCOLS = ["#4a4f5e", "#5a4a4a", "#3f5560", "#5b5a46", "#4d4560", "#3a4a3a", "#6a5a50", "#2f3a4f"]

def zombie(c, x, y, H, t, seed=0, face=1, alert=0.0, walk=True, alpha=1.0, dark=0.0, sil=False):
    rng = random.Random(seed)
    Hp = H * rng.uniform(0.9, 1.06)
    R = 0.13 * Hp; leg = 0.36 * Hp; torso = 0.3 * Hp; bw = 0.25 * Hp * rng.uniform(0.9, 1.15)
    skin = rng.choice(["#8fa58a", "#9aab8e", "#7f9a86", "#a3ad8f"]); cloth = rng.choice(ZCOLS); pants = rng.choice(["#2a2e38", "#3a3330", "#28323a"])
    if sil: skin = cloth = pants = "#0a0d14"
    sp = rng.uniform(0.35, 0.6)
    ph = (t * sp + rng.random()) if walk else rng.random() * 0.1
    c.save(); c.translate(x, y)
    src(c, "#000000", 0.25 * alpha); c.save(); c.scale(1, 0.22); c.arc(0, 0, bw * 0.75, 0, 2 * math.pi); c.restore(); c.fill()
    c.push_group()
    if face < 0: c.scale(-1, 1)
    hunch = 0.12 + 0.1 * math.sin(ph * 2 * math.pi) * 0.3 + rng.uniform(-0.05, 0.08)
    c.translate(0, -abs(math.sin(ph * 2 * math.pi)) * 0.01 * Hp)
    for i, sgn in enumerate((-1, 1)):
        a = math.sin(ph * 2 * math.pi + i * math.pi) * 0.22 if walk else 0
        c.save(); c.translate(sgn * bw * 0.2, -leg); c.rotate(a)
        lw = bw * 0.3; fill_rr(c, -lw / 2, 0, lw, leg * 0.96, lw * 0.3, pants)
        fill_rr(c, -lw * 0.6, leg * 0.9, lw * 1.4, lw * 0.45, lw * 0.2, "#1b1b1f" if not sil else pants)
        c.restore()
    c.translate(0, -leg); c.rotate(hunch); c.translate(0, leg)
    ty = -leg - torso
    def zarm(sgn, off):
        c.save(); c.translate(sgn * bw * 0.4, ty + torso * 0.1)
        a = -1.35 - alert * 0.25 + math.sin(t * 2 + seed + off) * 0.08
        c.rotate(a)
        aw = bw * 0.22; L = torso * 1.0
        fill_rr(c, -aw / 2, 0, aw, L, aw / 2, cloth if sgn < 0 else cloth); fill_rr(c, -aw / 2, L * 0.55, aw, L * 0.45, aw / 2, skin)
        src(c, skin); c.arc(0, L, aw * 0.55, 0, 2 * math.pi); c.fill()
        c.restore()
    zarm(-1, 0)
    fill_rr(c, -bw / 2, ty, bw, torso + bw * 0.1, bw * 0.25, cloth)
    if not sil:
        # torn hem
        src(c, cloth); c.move_to(-bw / 2, ty + torso)
        for i in range(6): c.line_to(-bw / 2 + (i + 0.5) * bw / 6, ty + torso + bw * (0.22 if i % 2 else 0.05))
        c.line_to(bw / 2, ty + torso); c.close_path(); c.fill()
        src(c, "#000000", 0.15); c.rectangle(-bw * 0.1, ty + torso * 0.3, bw * 0.3, bw * 0.12); c.fill()
    hy = ty - R * 0.85
    c.save(); c.translate(0, hy); c.rotate(0.25 * math.sin(t * 0.8 + seed) + 0.15); c.translate(0, -hy)
    d = dict(skin=skin, hc="#2a2a24", hair=rng.choice(["short", "messy", "buzz", "long", "fade"]), top="tee", tc=cloth, t2=cloth, acc=[])
    draw_head(c, "z", d, 0, hy, R, t, 0, "n", None, sil, False, True)
    c.restore()
    zarm(1, 1.3)
    _finish(c, alpha, Hp)
    c.restore()
