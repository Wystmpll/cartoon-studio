import math, random, cairo
from engine import *
from chars import person, zombie, P, register, load_library

GREEN_FOG = (0.55, 0.75, 0.6)

# ---------- atmosphere ----------
def fog(c, t, a=0.18, y0=600, y1=900, col=(0.7, 0.78, 0.9), n=7, seed=1):
    rng = random.Random(seed)
    for i in range(n):
        x = (rng.uniform(-200, W + 200) + t * rng.uniform(8, 22)) % (W + 400) - 200
        y = rng.uniform(y0, y1); r = rng.uniform(160, 300)
        g = cairo.RadialGradient(x, y, 0, x, y, r)
        g.add_color_stop_rgba(0, *col, a); g.add_color_stop_rgba(1, *col, 0)
        c.set_source(g); c.arc(x, y, r, 0, 2 * math.pi); c.fill()

def dust(c, t, n=40, a=0.35, seed=3, area=(0, 0, W, 820)):
    rng = random.Random(seed)
    x0, y0, w, h = area
    for i in range(n):
        x = x0 + (rng.random() * w + t * rng.uniform(-6, 6)) % w
        y = y0 + (rng.random() * h - t * rng.uniform(4, 14)) % h
        src(c, pal("#cfd8ff"), a * (0.4 + 0.6 * abs(math.sin(t + i)))); c.arc(x, y, rng.uniform(0.8, 1.8), 0, 2 * math.pi); c.fill()

def handheld(c, t, k=1.0):
    c.translate(math.sin(t * 1.7) * 3 * k + math.sin(t * 4.3) * 1.2 * k, math.cos(t * 1.3) * 2.5 * k)

def flash_red(c, t, a=0.25, speed=5):
    k = 0.5 + 0.5 * math.sin(t * speed)
    c.set_source_rgba(0.9, 0.1, 0.1, a * k); c.paint()

def light_cone(c, x, y, ang, length=520, spread=0.28, a=0.25, col=(1, 0.95, 0.75)):
    c.save(); c.translate(x, y); c.rotate(ang)
    g = cairo.LinearGradient(0, 0, length, 0)
    g.add_color_stop_rgba(0, *col, a); g.add_color_stop_rgba(1, *col, 0)
    c.set_source(g); c.move_to(0, 0); c.line_to(length, -length * spread); c.line_to(length, length * spread); c.close_path(); c.fill()
    c.restore()

def trees(c, y=820, seed=2, col="#0b1220", n=9):
    rng = random.Random(seed)
    for i in range(n):
        x = i * W / (n - 1) + rng.uniform(-30, 30); h = rng.uniform(140, 260); r = rng.uniform(50, 90)
        src(c, col); c.rectangle(x - 5, y - h * 0.5, 10, h * 0.5); c.fill()
        c.arc(x, y - h * 0.6, r, 0, 2 * math.pi); c.fill(); c.arc(x - r * 0.6, y - h * 0.45, r * 0.7, 0, 2 * math.pi); c.fill(); c.arc(x + r * 0.6, y - h * 0.45, r * 0.7, 0, 2 * math.pi); c.fill()

def lamp(c, x, y, t, on=True, flicker=False):
    src(c, pal("#1b2236")); c.rectangle(x - 3, y - 210, 6, 210); c.fill(); c.rectangle(x - 3, y - 210, 34, 5); c.fill()
    k = 1.0
    if flicker: k = 0.2 if (int(t * 13) % 7 == 0 or int(t * 7) % 11 == 0) else 1.0
    if on:
        glow(c, x + 30, y - 200, 160, (1, 0.85, 0.5), 0.35 * k)
        light_cone(c, x + 30, y - 200, math.pi / 2, 210, 0.45, 0.12 * k)

# ---------- exterior ----------
def ext_dorm(c, t, cx=0, cy=-300, s=1.0, sy=520, lit=None, door_red=0.0, sealed=0.0, zomb=0, zseed=1, fog_a=0.15, labels=True):
    sky(c, t); moon(c, 610, 120)
    c.save(); cam(c, cx, cy, s, sy)
    building(c, t, lit, door_red=door_red, sealed=sealed, labels=labels)
    for i in range(zomb):
        rng = random.Random(zseed * 100 + i)
        zx = -300 + (rng.uniform(0, 600) + t * rng.uniform(-8, 8))
        zombie(c, zx, 0, 64, t, seed=zseed * 50 + i, face=1 if rng.random() > .5 else -1)
    c.restore()
    gy = sy + (0 - cy) * s
    ground(c, gy)
    fog(c, t, fog_a, gy - 120, gy + 80)

def lit_rand(k=1.0, seed=1, frac=0.6):
    def f(blk, fl, i):
        r = random.Random(hash((blk, fl, i, seed))).random()
        return k * (0.85 if r < frac else 0.0)
    return f

# ---------- interiors ----------
def room(c, kind, t, dark=0.0, moon=True):
    if kind == "roomB":
        room_bg(c, "dorm", t)
        if moon: glow(c, 365, 290, 260, (0.6, 0.7, 1.0), 0.12); light_cone(c, 365, 290, math.pi * 0.62, 600, 0.3, 0.06, (0.7, 0.8, 1))
    elif kind == "roomA":
        room_bg(c, "dorm", t)
        src(c, pal("#2a3550")); c.rectangle(250, 520, 220, 26); c.fill(); src(c, pal("#3b4a72")); c.rectangle(250, 500, 220, 22); c.fill()
        if moon: glow(c, 365, 290, 260, (0.6, 0.7, 1.0), 0.12)
    elif kind == "hallglass":
        room_bg(c, "hall", t)
        # glass doors
        src(c, pal("#9fb6d8"), 0.18); c.rectangle(280, 430, 160, 370); c.fill()
        src(c, pal("#c8d6ee"), 0.25); c.set_line_width(2)
        for i in range(3): c.move_to(300 + i * 50, 450); c.line_to(330 + i * 50, 520); c.stroke()
    elif kind == "teach":
        src(c, pal("#1a2238")); c.rectangle(0, 0, W, FLOOR_Y); c.fill()
        # vanishing corridor
        src(c, pal("#141b2e")); c.move_to(0, 0); c.line_to(W, 0); c.line_to(440, 330); c.line_to(280, 330); c.close_path(); c.fill()
        src(c, pal("#0f1524")); c.move_to(0, FLOOR_Y); c.line_to(W, FLOOR_Y); c.line_to(440, 470); c.line_to(280, 470); c.close_path(); c.fill()
        src(c, pal("#1e2742")); c.move_to(0, 0); c.line_to(280, 330); c.line_to(280, 470); c.line_to(0, FLOOR_Y); c.close_path(); c.fill()
        c.move_to(W, 0); c.line_to(440, 330); c.line_to(440, 470); c.line_to(W, FLOOR_Y); c.close_path(); c.fill()
        src(c, pal("#0a0e18")); c.rectangle(280, 330, 160, 140); c.fill()
        for i in range(5):
            k = i / 5; x0 = lerp(0, 280, k); y0 = lerp(0, 330, k); y1 = lerp(FLOOR_Y, 470, k)
            src(c, pal("#2a3456")); c.rectangle(x0 + 10, y0 + (y1 - y0) * 0.35, (1 - k) * 40 + 8, (y1 - y0) * 0.6); c.fill()
            x0 = lerp(W, 440, k); src(c, pal("#2a3456")); c.rectangle(x0 - (1 - k) * 40 - 18, y0 + (y1 - y0) * 0.35, (1 - k) * 40 + 8, (y1 - y0) * 0.6); c.fill()
            src(c, C["grn"], 0.5); c.rectangle(lerp(320, 345, k) + 0 * k, lerp(40, 335, k), 30 * (1 - k) + 6, 12 * (1 - k) + 3); c.fill()
        text(c, "教学西楼", 120, 120, 30, pal("#3b4a72"), font=CJK)
        src(c, C["floor"]); c.rectangle(0, FLOOR_Y, W, H - FLOOR_Y); c.fill(); src(c, pal("#2a3550")); c.rectangle(0, FLOOR_Y, W, 4); c.fill()
    else:
        room_bg(c, kind, t)
    if dark > 0: darken(c, dark)

def floor_y(): return FLOOR_Y

# ---------- crowd ----------
def crowd(c, t, n, x0, x1, y, Hh, seed=1, face=None, alert=0.0, walk=True, depth=0, sil=False, speed=0.0, alpha=1.0):
    rng = random.Random(seed)
    items = []
    for i in range(n):
        x = rng.uniform(x0, x1) + t * speed * rng.uniform(0.6, 1.2)
        yy = y + rng.uniform(-depth, depth)
        items.append((yy, x, i))
    items.sort()
    for yy, x, i in items:
        sc = 1 + (yy - y) / 600
        f = face if face is not None else (1 if rng.random() > .5 else -1)
        zombie(c, x, yy, Hh * sc, t, seed=seed * 31 + i, face=f, alert=alert, walk=walk, sil=sil, alpha=alpha)

# ---------- phone chat ----------
NAMECOL = {}
def namecol(n):
    if n in NAMECOL: return NAMECOL[n]
    d = P.get(n)
    if not d: return "#ffffff"
    r, g, b, _ = hexc(d["tc"]); lum = 0.3 * r + 0.59 * g + 0.11 * b
    return d["tc"] if lum > 0.35 else "#9aa3b8"

def phone(c, t, msgs, x=W / 2, y=440, s=1.0, title=None, typing=None, t0=0.0):
    title = title or tr("ЧАТ", "GROUP CHAT")
    """msgs: list of (time, name, text). shows those with time<=t, last 5."""
    k = eout(seg(t, t0, t0 + 0.35))
    if k <= 0: return
    c.save(); c.translate(x, y + (1 - k) * 200); c.scale(s, s)
    w, h = 400, 640
    glow(c, 0, 0, 420, (0.5, 0.7, 1.0), 0.18)
    fill_rr(c, -w / 2 - 12, -h / 2 - 12, w + 24, h + 24, 46, "#0b0d12")
    fill_rr(c, -w / 2, -h / 2, w, h, 36, "#151a26")
    fill_rr(c, -w / 2, -h / 2, w, 78, 36, "#1e2536"); src(c, "#1e2536"); c.rectangle(-w / 2, -h / 2 + 40, w, 38); c.fill()
    text(c, title, 0, -h / 2 + 50, 22, "#ffffff")
    text(c, "14 участников", 0, -h / 2 + 70, 12, "#8a93a6", font=XB)
    shown = [m for m in msgs if m[0] <= t][-5:]
    yy = h / 2 - 30
    if typing and typing[0] <= t < typing[1]:
        fill_rr(c, -w / 2 + 16, yy - 40, 90, 36, 16, "#232b3d")
        for i in range(3):
            a = 0.4 + 0.6 * abs(math.sin(t * 6 + i))
            src(c, "#cfd6e6", a); c.arc(-w / 2 + 40 + i * 20, yy - 22, 5, 0, 2 * math.pi); c.fill()
        yy -= 52
    for (tm, nm, tx) in reversed(shown):
        lines = wrap(c, tx, 19, w - 110)
        bh = 30 + 26 * len(lines)
        kk = eout(seg(t, tm, tm + 0.25))
        c.save(); c.translate(0, (1 - kk) * 20)
        fill_rr(c, -w / 2 + 16, yy - bh, w - 60, bh, 16, "#232b3d", kk)
        text(c, nm, -w / 2 + 32, yy - bh + 22, 15, namecol(nm), anchor="l", a=kk)
        for i, ln in enumerate(lines):
            text(c, ln, -w / 2 + 32, yy - bh + 48 + i * 26, 19, "#eef1f7", font=XB, anchor="l", a=kk)
        c.restore()
        yy -= bh + 12
        if yy < -h / 2 + 100: break
    c.restore()

def wrap(c, s, size, maxw):
    words = s.split(); lines = []; cur = ""
    for w in words:
        tt = (cur + " " + w).strip()
        if text_w(c, tt, size, XB) > maxw and cur:
            lines.append(cur); cur = w
        else: cur = tt
    if cur: lines.append(cur)
    return lines

# ---------- campus map ----------
MAP_PTS = {
    "dorm": (0, 330), "yard": (0, 190), "west": (-130, 40), "east": (130, 40),
    "lib": (40, -170), "qizhen": (40, -40), "stad": (-150, -330),
}

def campus_map(  # NPU Chang'an campus preset; for other places use site_map()
        c, t, path=None, path_k=0.0, dots=(), cx=W / 2, cy=440, s=1.0, hl=None, hand=False, zom=0):
    c.save(); c.translate(cx, cy); c.scale(s, s)
    paper = pal("#e9dfc6") if hand else pal("#121a2b")
    ink = pal("#3a3328") if hand else pal("#4a5778")
    fill_rr(c, -320, -430, 640, 860, 18, paper)
    if hand:
        src(c, pal("#000000"), 0.06)
        for i in range(30): c.rectangle(-320, -430 + i * 29, 640, 1); c.fill()
    def box(x, y, w, h, label, sub=None, col=None, key=None):
        hk = (hl == key) if key else False
        if hand:
            src(c, ink); c.set_line_width(3); c.rectangle(x - w / 2, y - h / 2, w, h); c.stroke()
        else:
            fill_rr(c, x - w / 2, y - h / 2, w, h, 8, col or pal("#1e2740"))
            src(c, C["yel"] if hk else pal("#2c3754")); c.set_line_width(3 if hk else 2); rrect(c, x - w / 2, y - h / 2, w, h, 8); c.stroke()
        text(c, label, x, y + 6, 18, ink if hand else pal("#aab3c8"), font=BLACK)
        if sub: text(c, sub, x, y + 26, 13, ink if hand else pal("#6f7a96"), font=CJK)
    # lake around library
    if not hand:
        src(c, pal("#16304a")); c.save(); c.translate(40, -170); c.scale(1.4, 0.8); c.arc(0, 0, 120, 0, 2 * math.pi); c.restore(); c.fill()
    else:
        src(c, pal("#5a7a9a"), 0.5); c.save(); c.translate(40, -170); c.scale(1.4, 0.8); c.arc(0, 0, 120, 0, 2 * math.pi); c.restore(); c.fill()
    box(0, 360, 300, 80, "ОБЩАГА", "留学生公寓", key="dorm")
    box(0, 205, 160, 60, "ДВОР", None, pal("#15202e"), key="yard")
    box(-120, 40, 200, 90, "ЗАПАДНЫЙ", "教学西楼", key="west")
    box(120, 40, 200, 90, "ВОСТОЧНЫЙ", "教学东楼", key="east")
    src(c, C["yel"] if not hand else ink, 0.6); c.rectangle(-20, 30, 40, 20); c.fill()
    box(40, -170, 160, 80, "БИБЛИОТЕКА", "图书馆", pal("#223a5a"), key="lib")
    box(-170, -330, 220, 110, "СТАДИОН", "体育场", pal("#1d3326"), key="stad")
    box(170, -330, 150, 70, "", None, pal("#1e2740"))
    text(c, "启真楼", 170, -324, 16, ink if hand else pal("#6f7a96"), font=CJK)
    # zombie dots
    rng = random.Random(7)
    for i in range(zom):
        zx, zy = rng.uniform(-300, 300), rng.uniform(-410, 410)
        zx += math.sin(t * 0.7 + i) * 6; zy += math.cos(t * 0.5 + i) * 6
        src(c, pal("#9bd36a") if not hand else pal("#8a2a2a"), 0.75); c.arc(zx, zy, 5, 0, 2 * math.pi); c.fill()
    if path and path_k > 0:
        pts = path
        segl = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
        L = sum(segl) * clamp(path_k)
        c.set_dash([12, 9]); src(c, C["red"] if hand else C["yel"]); c.set_line_width(6)
        c.move_to(*pts[0]); acc = 0; end = pts[0]
        for i, l in enumerate(segl):
            if acc + l >= L:
                f = (L - acc) / l; end = (lerp(pts[i][0], pts[i + 1][0], f), lerp(pts[i][1], pts[i + 1][1], f)); c.line_to(*end); break
            c.line_to(*pts[i + 1]); acc += l; end = pts[i + 1]
        c.stroke(); c.set_dash([])
        for col, ox in dots:
            src(c, col); c.arc(end[0] + ox, end[1], 13, 0, 2 * math.pi); c.fill()
            src(c, pal("#ffffff")); c.set_line_width(2.5); c.arc(end[0] + ox, end[1], 13, 0, 2 * math.pi); c.stroke()
    c.restore()

ROUTE = [(0, 330), (0, 205), (-120, 40), (120, 40), (120, -60), (40, -170), (-60, -250), (-150, -310)]

# ---------- vehicles / props ----------
def heli(c, x, y, s, t, light=True):
    c.save(); c.translate(x, y); c.scale(s, s)
    if light: light_cone(c, -10, 40, math.pi / 2 + 0.15, 700, 0.22, 0.18)
    src(c, pal("#1b2133")); c.save(); c.scale(1.6, 1); c.arc(0, 0, 50, 0, 2 * math.pi); c.restore(); c.fill()
    c.rectangle(60, -14, 140, 22); c.fill()
    c.move_to(190, -14); c.line_to(215, -50); c.line_to(225, -50); c.line_to(210, 8); c.close_path(); c.fill()
    src(c, pal("#3b6fb0"), 0.8); c.save(); c.scale(1.5, 1); c.arc(-28, -8, 24, math.pi, 2 * math.pi); c.restore(); c.fill()
    src(c, pal("#2a3146")); c.rectangle(-60, 48, 120, 6); c.fill(); c.rectangle(-40, 30, 6, 20); c.fill(); c.rectangle(34, 30, 6, 20); c.fill()
    src(c, pal("#2a3146")); c.rectangle(-4, -66, 8, 16); c.fill()
    ph = (t * 18) % 1
    src(c, pal("#aab3c8"), 0.6); c.set_line_width(5)
    c.move_to(-170 * math.cos(ph * math.pi), -66); c.line_to(170 * math.cos(ph * math.pi), -66); c.stroke()
    src(c, C["red"] if int(t * 2) % 2 else pal("#550000")); c.arc(210, -46, 5, 0, 2 * math.pi); c.fill()
    c.restore()

def speaker(c, x, y, s=1.0, t=0, on=False):
    c.save(); c.translate(x, y); c.scale(s, s)
    fill_rr(c, -40, -70, 80, 110, 12, pal("#1b1f2a"))
    src(c, pal("#2e3546")); c.arc(0, -35, 22, 0, 2 * math.pi); c.fill(); c.arc(0, 10, 14, 0, 2 * math.pi); c.fill()
    src(c, pal("#0e1118")); c.arc(0, -35, 10, 0, 2 * math.pi); c.fill()
    if on:
        for i in range(3):
            r = 40 + ((t * 60 + i * 30) % 90)
            src(c, C["yel"], max(0, 0.6 - r / 160)); c.set_line_width(4); c.arc(0, -30, r, -0.6, 0.6); c.stroke(); c.arc(0, -30, r, math.pi - 0.6, math.pi + 0.6); c.stroke()
        src(c, C["grn"]); c.arc(28, 28, 4, 0, 2 * math.pi); c.fill()
    c.restore()

def noodle(c, x, y, s=1.0):
    portion(c, x, y, s)

def notes(c, x, y, t, t0):
    if t < t0: return
    for i in range(5):
        tt = (t - t0 + i * 0.4) % 2.0
        a = 1 - tt / 2.0
        xx = x + math.sin(tt * 3 + i) * 40 + (i - 2) * 30; yy = y - tt * 120
        src(c, C["yel"], a); c.arc(xx, yy, 7, 0, 2 * math.pi); c.fill(); c.rectangle(xx + 5, yy - 28, 3, 28); c.fill()

def closeup2(c, name, t, Hh=900, x=360, head_y=420, **kw):
    d = P[name]; Hp = Hh * d["h"] / 185
    # head center = feet - leg - torso - R*0.92 => feet = head_y + (0.36 + 0.29 + 0.135*0.92) * Hp
    return person(c, name, x, head_y + (0.36 + 0.29 + 0.124) * Hp, Hh, t, **kw)

def scene_title(c, s, t, t0=0.05, y=110, col="yel", size=18, fg="#111111"):
    chip(c, s, W / 2, y, t, t0, col, size, fg=fg)

# =====================================================================
# Generic sets (all colours go through pal() so styles can re-colour them)
# =====================================================================
def panel(c, x, y, w, h, fn, label=None, lab_col="dim", t=0, t0=0.0, border=None, view_h=540):
    """Draw a full-stage scene fn(c) shrunk into a rectangle (split screens, comic panels)."""
    k = eout(seg(t, t0, t0 + 0.35))
    if k <= 0: return
    c.save(); c.translate(0, (1 - k) * 40)
    c.rectangle(x, y, w, h); c.clip()
    src(c, pal("#161d31")); c.paint()
    sc = min(w / W, h / view_h)
    c.save(); c.translate(x + (w - W * sc) / 2, y + h - 820 * sc); c.scale(sc, sc)
    if W * sc < w:
        src(c, pal("#161d31")); c.rectangle(-((w - W * sc) / 2) / sc, 0, w / sc, 820); c.fill()
    fn(c)
    c.restore(); c.reset_clip()
    src(c, border or (STYLE.get("ink") or pal(C["edge"]))); c.set_line_width(4 if not STYLE.get("ink") else 6); c.rectangle(x, y, w, h); c.stroke()
    if label: chip(c, label, x + w / 2, y + 22, t, t0 + 0.1, lab_col, 15, fg="#111111" if lab_col == "yel" else "#ffffff")
    c.restore()

def head_pos(name, x, y, Hh):
    """Screen position (x, y) of a character's head centre and head radius R."""
    Hp = Hh * P[name]["h"] / 185; R = 0.135 * Hp * STYLE.get("head_scale", 1.0)
    return x, y - (0.36 + 0.29) * Hp - R * 0.92, R

def ear_phone(c, name, x, y, Hh, side=1):
    hx, hy, R = head_pos(name, x, y, Hh)
    c.save(); c.translate(hx + side * R * 1.05, hy + R * 0.1); c.rotate(side * 0.2)
    fill_rr(c, -R * 0.18, -R * 0.45, R * 0.36, R * 0.85, R * 0.08, "#111318"); fill_rr(c, -R * 0.13, -R * 0.38, R * 0.26, R * 0.7, R * 0.05, "#7cc7ff")
    src(c, P[name]["skin"]); c.arc(side * R * 0.12, R * 0.35, R * 0.22, 0, 2 * math.pi); c.fill()
    c.restore()

def street(c, t, night=True, shops=True):
    sky(c, t, 0.0 if night else 1.0)
    if not night:
        g = cairo.LinearGradient(0, 0, 0, 800); g.add_color_stop_rgb(0, *hexc(pal("#8ec5ff"))[:3]); g.add_color_stop_rgb(1, *hexc(pal("#e8f2ff"))[:3]); c.set_source(g); c.rectangle(0, 0, W, 800); c.fill()
    rng = random.Random(4)
    x = -20
    while x < W:
        w = rng.uniform(110, 180); h = rng.uniform(260, 520)
        src(c, pal(rng.choice(["#1a2338", "#1d2740", "#212b44"]))); c.rectangle(x, 800 - h, w - 6, h); c.fill()
        for r in range(int(h // 60) - 1):
            for k in range(int(w // 45)):
                lit = rng.random() < (0.45 if night else 0.0)
                src(c, pal("#f2c14e") if lit else pal("#2a3552"), 0.9); c.rectangle(x + 12 + k * 42, 800 - h + 20 + r * 60, 24, 30); c.fill()
        if shops and rng.random() < 0.6:
            fill_rr(c, x + 10, 690, w - 26, 34, 6, pal(rng.choice(["#e5484d", "#4c8bf5", "#3ecf8e", "#f5c542"])))
        x += w
    src(c, pal("#232b3d")); c.rectangle(0, 800, W, H - 800); c.fill()
    src(c, pal("#3a4256")); c.rectangle(0, 800, W, 10); c.fill()
    for i in range(6): src(c, pal("#cfd6e6"), 0.5); c.rectangle(i * 140 + 20, 880, 70, 8); c.fill()

def forest(c, t, night=True):
    sky(c, t, 0.0 if night else 1.0)
    for layer, (col, y, n, sc) in enumerate((("#0f1a24", 700, 10, 1.2), ("#0b1420", 760, 8, 1.6), ("#08101a", 820, 6, 2.2))):
        rng = random.Random(10 + layer)
        for i in range(n):
            x = rng.uniform(-40, W + 40); hh = rng.uniform(200, 380) * sc
            src(c, pal(col)); c.move_to(x, y - hh); c.line_to(x - 60 * sc, y); c.line_to(x + 60 * sc, y); c.close_path(); c.fill()
    src(c, pal("#0a0f16")); c.rectangle(0, 820, W, H - 820); c.fill()

def classroom(c, t, dark=0.0):
    room_bg(c, "kitchen", t)
    src(c, pal("#1d2a22")); c.rectangle(80, 170, 560, 260); c.fill(); src(c, pal("#6a5a40")); c.set_line_width(10); c.rectangle(80, 170, 560, 260); c.stroke()
    src(c, pal("#e8e8e0"), 0.75); c.set_line_width(3)
    for i in range(4): c.move_to(120, 220 + i * 50); c.line_to(120 + (300 + i * 37) % 420, 220 + i * 50); c.stroke()
    for i in range(3):
        src(c, pal("#3a4870")); c.rectangle(60 + i * 220, 650, 180, 16); c.fill(); src(c, pal("#2a3550")); c.rectangle(70 + i * 220, 666, 10, 134); c.fill(); c.rectangle(220 + i * 220, 666, 10, 134); c.fill()
    darken(c, dark)

def canteen(c, t, dark=0.0):
    room_bg(c, "kitchen", t)
    for i in range(3):
        src(c, pal("#3a4870")); c.rectangle(40 + i * 230, 640, 200, 18); c.fill()
        for k in range(3): portion(c, 80 + i * 230 + k * 55, 640, 0.9)
    text(c, "食堂", 600, 140, 40, pal("#3b4a72"), font=CJK)
    darken(c, dark)

def rooftop(c, t, night=True):
    sky(c, t, 0.0 if night else 1.0); moon(c, 600, 140)
    rng = random.Random(9)
    for i in range(14):
        x = i * 55; h = rng.uniform(60, 260)
        src(c, pal("#141c2e")); c.rectangle(x, 640 - h, 52, h); c.fill()
        for k in range(int(h // 40)):
            if rng.random() < 0.4: src(c, pal("#f2c14e"), 0.8); c.rectangle(x + 10 + (k % 2) * 20, 640 - h + 10 + k * 40, 10, 14); c.fill()
    src(c, pal("#2a3146")); c.rectangle(0, 700, W, H - 700); c.fill(); src(c, pal("#3a4256")); c.rectangle(0, 690, W, 14); c.fill()
    for i in range(8): src(c, pal("#4c5d8e")); c.rectangle(i * 95, 640, 6, 60); c.fill()
    src(c, pal("#4c5d8e")); c.rectangle(0, 650, W, 5); c.fill()

def iso_room(c, t, cx=360, cy=520, size=300, floor="#2a3550", wl="#1d2740", wr="#232c46", tiles=True):
    """Isometric room (isometric style). Returns function (u,v)->(x,y) to place things on the floor (u,v in 0..1)."""
    s = size
    def P2(u, v): return (cx + (u - v) * s, cy + (u + v) * s * 0.5 - s * 0.5)
    a, b, cc, d = P2(0, 0), P2(1, 0), P2(1, 1), P2(0, 1)
    src(c, pal(wl)); c.move_to(*a); c.line_to(*d); c.line_to(d[0], d[1] - s * 0.9); c.line_to(a[0], a[1] - s * 0.9); c.close_path(); c.fill()
    src(c, pal(wr)); c.move_to(*a); c.line_to(*b); c.line_to(b[0], b[1] - s * 0.9); c.line_to(a[0], a[1] - s * 0.9); c.close_path(); c.fill()
    src(c, pal(floor)); c.move_to(*a); c.line_to(*b); c.line_to(*cc); c.line_to(*d); c.close_path(); c.fill()
    if tiles:
        src(c, pal("#33405f"), 0.6); c.set_line_width(1.5)
        for i in range(1, 6):
            p, q = P2(i / 6, 0), P2(i / 6, 1); c.move_to(*p); c.line_to(*q); c.stroke()
            p, q = P2(0, i / 6), P2(1, i / 6); c.move_to(*p); c.line_to(*q); c.stroke()
    return P2

def iso_box(c, P2, u, v, du, dv, hgt, top="#3a4870", left="#2a3550", right="#33405f"):
    s = P2(1, 0)[0] - P2(0, 0)[0]
    A, B, Cc, D = P2(u, v), P2(u + du, v), P2(u + du, v + dv), P2(u, v + dv)
    h = hgt * s
    src(c, pal(left)); c.move_to(*D); c.line_to(*Cc); c.line_to(Cc[0], Cc[1] - h); c.line_to(D[0], D[1] - h); c.close_path(); c.fill()
    src(c, pal(right)); c.move_to(*B); c.line_to(*Cc); c.line_to(Cc[0], Cc[1] - h); c.line_to(B[0], B[1] - h); c.close_path(); c.fill()
    src(c, pal(top)); c.move_to(A[0], A[1] - h); c.line_to(B[0], B[1] - h); c.line_to(Cc[0], Cc[1] - h); c.line_to(D[0], D[1] - h); c.close_path(); c.fill()

def paper_bg(c, kind="notebook"):
    """notebook (lined, margin), graph (squares), cork (pinboard)."""
    if kind == "cork":
        src(c, "#b58b5a"); c.paint(); rng = random.Random(2)
        for i in range(900):
            src(c, rng.choice(["#a07848", "#c89c68", "#8f6a3e"]), 0.6); c.arc(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1, 3), 0, 2 * math.pi); c.fill()
        return
    src(c, "#f7f3e8"); c.paint()
    if kind == "graph":
        src(c, "#9cc3e6", 0.5); c.set_line_width(1)
        for i in range(0, max(W, H), 30): c.move_to(i, 0); c.line_to(i, H); c.move_to(0, i); c.line_to(W, i)
        c.stroke(); return
    src(c, "#9cc3e6", 0.7); c.set_line_width(1.5)
    for y in range(120, H, 38): c.move_to(0, y); c.line_to(W, y)
    c.stroke(); src(c, "#ee8888", 0.8); c.set_line_width(2); c.move_to(70, 0); c.line_to(70, H); c.stroke()

def polaroid(c, x, y, w, h, fn, rot=0.0, caption=None, t=0, t0=0.0):
    """Scene fn(c) shown as a pinned photo (true-crime / scrapbook)."""
    k = eout(seg(t, t0, t0 + 0.3))
    if k <= 0: return
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(k, k)
    src(c, "#000000", 0.35); c.rectangle(-w / 2 + 6, -h / 2 + 8, w, h + 50); c.fill()
    src(c, "#f4f1e8"); c.rectangle(-w / 2, -h / 2, w, h + 50); c.fill()
    c.save(); c.rectangle(-w / 2 + 14, -h / 2 + 14, w - 28, h - 28); c.clip()
    sc = (w - 28) / W; c.translate(-w / 2 + 14, -h / 2 + 14 + (h - 28) - 820 * sc); c.scale(sc, sc); fn(c)
    c.restore()
    if caption: text(c, caption, 0, h / 2 + 28, 20, "#2a2a2a", font="DejaVu Sans Mono")
    src(c, "#c4312f"); c.arc(0, -h / 2 + 4, 8, 0, 2 * math.pi); c.fill()
    c.restore()

def red_string(c, pts, k=1.0):
    src(c, "#c4312f"); c.set_line_width(3)
    c.move_to(*pts[0])
    for p in pts[1:]: c.line_to(lerp(pts[0][0], p[0], 1) if k >= 1 else p[0], p[1])
    c.stroke()

def speed_lines(c, t, cx=W / 2, cy=470, n=40, a=0.5, col="#ffffff"):
    rng = random.Random(int(t * 12))
    for i in range(n):
        ang = rng.uniform(0, 2 * math.pi); r0 = rng.uniform(260, 380); r1 = r0 + rng.uniform(200, 500)
        src(c, col, a * rng.uniform(0.4, 1)); c.set_line_width(rng.uniform(2, 6))
        c.move_to(cx + math.cos(ang) * r0, cy + math.sin(ang) * r0); c.line_to(cx + math.cos(ang) * r1, cy + math.sin(ang) * r1); c.stroke()

def burst(c, s, x, y, t, t0, size=70, col="#f5c542", fg="#111111", rot=-0.1):
    """Comic sound-effect burst: БАМ!, БАХ!, ХРЯСЬ!"""
    k = pop(t, t0, 0.25)
    if k <= 0: return
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(k, k)
    w = text_w(c, s, size) * 0.75 + 40
    src(c, "#111111"); c.move_to(w, 0)
    for i in range(1, 25):
        a = i * 2 * math.pi / 24; r = (w + 14) if i % 2 else (w * 0.72 + 8)
        c.line_to(math.cos(a) * r, math.sin(a) * r * 0.62)
    c.close_path(); c.fill()
    src(c, col); c.move_to(w - 8, 0)
    for i in range(1, 25):
        a = i * 2 * math.pi / 24; r = (w) if i % 2 else (w * 0.72)
        c.line_to(math.cos(a) * r, math.sin(a) * r * 0.62)
    c.close_path(); c.fill()
    text(c, s, 0, size * 0.36, size, fg)
    c.restore()

def rain(c, t, a=0.35, n=120, slant=0.25, seed=1):
    rng = random.Random(seed)
    src(c, "#aac4ee", a); c.set_line_width(1.5)
    for i in range(n):
        x = (rng.uniform(0, W) + t * 160 * slant) % (W + 100) - 50
        y = (rng.uniform(0, H) + t * 900) % H
        c.move_to(x, y); c.line_to(x + 14 * slant, y + 28)
    c.stroke()

def snow(c, t, n=80, seed=2):
    rng = random.Random(seed)
    for i in range(n):
        x = (rng.uniform(0, W) + math.sin(t + i) * 20) % W; y = (rng.uniform(0, H) + t * rng.uniform(30, 70)) % H
        src(c, "#ffffff", 0.8); c.arc(x, y, rng.uniform(1.5, 3.5), 0, 2 * math.pi); c.fill()

def fire(c, x, y, s, t):
    for i in range(14):
        ph = (t * 1.6 + i * 0.13) % 1
        xx = x + math.sin(i * 2.1 + t * 3) * 20 * s; yy = y - ph * 140 * s; r = (1 - ph) * 34 * s + 4
        col = (1, 0.85 - ph * 0.6, 0.2) if ph < 0.6 else (0.9, 0.3, 0.1)
        c.set_source_rgba(*col, (1 - ph) * 0.85); c.arc(xx, yy, r, 0, 2 * math.pi); c.fill()
    glow(c, x, y - 40 * s, 180 * s, (1, 0.6, 0.2), 0.35)

def explosion(c, x, y, t, t0, s=1.0):
    k = seg(t, t0, t0 + 0.8)
    if k <= 0 or k >= 1: return
    for i in range(18):
        a = i * 2 * math.pi / 18; r = eout(k) * 220 * s
        c.set_source_rgba(1, 0.75 - 0.5 * k, 0.2, 1 - k); c.arc(x + math.cos(a) * r, y + math.sin(a) * r * 0.8, (1 - k) * 40 * s + 6, 0, 2 * math.pi); c.fill()
    glow(c, x, y, 400 * s, (1, 0.7, 0.3), 0.6 * (1 - k))
    c.set_source_rgba(1, 1, 0.9, max(0, 0.7 - k * 3)); c.paint()

def heart(c, x, y, s=1.0, col="#ff6f91", a=1.0):
    src(c, col, a); c.save(); c.translate(x, y); c.scale(s, s)
    c.move_to(0, 10); c.curve_to(-26, -8, -12, -26, 0, -12); c.curve_to(12, -26, 26, -8, 0, 10); c.fill(); c.restore()

def arrow(c, x0, y0, x1, y1, t, t0, col="yel", w=6):
    k = eout(seg(t, t0, t0 + 0.5))
    if k <= 0: return
    xe, ye = lerp(x0, x1, k), lerp(y0, y1, k)
    src(c, C.get(col, col)); c.set_line_width(w); c.move_to(x0, y0); c.line_to(xe, ye); c.stroke()
    ang = math.atan2(ye - y0, xe - x0)
    c.move_to(xe, ye); c.line_to(xe - 22 * math.cos(ang - 0.45), ye - 22 * math.sin(ang - 0.45)); c.line_to(xe - 22 * math.cos(ang + 0.45), ye - 22 * math.sin(ang + 0.45)); c.close_path(); c.fill()

def site_map(c, t, places, route=None, route_k=0.0, dots=(), hl=None, hand=False, cx=W / 2, cy=440, s=1.0, marks=0, water=()):
    """Generic top-down map. places: list of (key, x, y, w, h, label, sub). water: list of (x, y, rx, ry)."""
    c.save(); c.translate(cx, cy); c.scale(s, s)
    paper = "#e9dfc6" if hand else pal("#121a2b"); ink = "#3a3328" if hand else pal("#4a5778")
    fill_rr(c, -320, -430, 640, 860, 18, paper)
    for (wx, wy, rx, ry) in water:
        src(c, "#5a7a9a" if hand else pal("#16304a"), 0.6 if hand else 1); c.save(); c.translate(wx, wy); c.scale(rx / 100, ry / 100); c.arc(0, 0, 100, 0, 2 * math.pi); c.restore(); c.fill()
    for key, x, y, w, h, lab, sub in places:
        if hand:
            src(c, ink); c.set_line_width(3); c.rectangle(x - w / 2, y - h / 2, w, h); c.stroke()
        else:
            fill_rr(c, x - w / 2, y - h / 2, w, h, 8, pal("#1e2740"))
            src(c, C["yel"] if hl == key else pal("#2c3754")); c.set_line_width(3); rrect(c, x - w / 2, y - h / 2, w, h, 8); c.stroke()
        text(c, lab, x, y + 6, 18, ink if hand else pal("#aab3c8"))
        if sub: text(c, sub, x, y + 26, 13, ink if hand else pal("#6f7a96"), font=CJK)
    rng = random.Random(7)
    for i in range(marks):
        zx, zy = rng.uniform(-300, 300) + math.sin(t * 0.7 + i) * 6, rng.uniform(-410, 410) + math.cos(t * 0.5 + i) * 6
        src(c, "#8a2a2a" if hand else "#9bd36a", 0.75); c.arc(zx, zy, 5, 0, 2 * math.pi); c.fill()
    if route and route_k > 0:
        segl = [math.hypot(route[i + 1][0] - route[i][0], route[i + 1][1] - route[i][1]) for i in range(len(route) - 1)]
        L = sum(segl) * clamp(route_k); acc = 0; end = route[0]
        c.set_dash([12, 9]); src(c, C["red"] if hand else C["yel"]); c.set_line_width(6); c.move_to(*route[0])
        for i, l in enumerate(segl):
            if acc + l >= L:
                f = (L - acc) / l; end = (lerp(route[i][0], route[i + 1][0], f), lerp(route[i][1], route[i + 1][1], f)); c.line_to(*end); break
            c.line_to(*route[i + 1]); acc += l; end = route[i + 1]
        c.stroke(); c.set_dash([])
        for col, ox in dots:
            src(c, col); c.arc(end[0] + ox, end[1], 13, 0, 2 * math.pi); c.fill(); src(c, "#ffffff"); c.set_line_width(2.5); c.arc(end[0] + ox, end[1], 13, 0, 2 * math.pi); c.stroke()
    c.restore()

def sit(c, name, x, y, Hh, t, **kw):
    """Character sitting behind a table/bench edge at y (legs hidden): draws upper body only."""
    c.save(); c.rectangle(0, 0, W, y); c.clip()
    Hp = Hh * P[name]["h"] / 185
    person(c, name, x, y + 0.36 * Hp * 0.9, Hh, t, **kw)
    c.restore()

def lying(c, name, x, y, Hh, t, rot=-math.pi / 2, **kw):
    c.save(); c.translate(x, y); c.rotate(rot); person(c, name, 0, 0, Hh, t, bob=False, **kw); c.restore()
