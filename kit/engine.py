import cairo, math, random

W, H = 720, 1280
LANG = {"code": "ru"}   # set by render.load_project from project.json "lang"

def tr(ru, en):
    """Pick the label for the project language."""
    return en if LANG["code"] == "en" else ru
FPS = 30
BLACK = "Inter Black"; XB = "Inter ExtraBold"; CJK = "Noto Sans CJK SC"

def hexc(h, a=1.0):
    h = h.lstrip("#"); return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)

C = dict(
    bg1="#0b1120", bg2="#131c31", bld="#1a2338", bld2="#212b44", edge="#2c3754", win="#263049", lit="#f2c14e",
    yel="#f5c542", red="#e5484d", grn="#3ecf8e", blu="#4c8bf5", paper="#f1e8d0", ink="#1b1b1f", white="#ffffff",
    grey="#7d869c", dim="#4a5470", skin="#f0c39b", pants="#262d40", floor="#0d121e", wall="#182036", wall2="#1d2740",
)


# ---------- style hooks ----------
STYLE = dict(name="survival", bgmap=None, head_scale=1.0, eye="round", outline=0.0, outline_col="#111111",
             drop_shadow=0.0, cel=0.0, clay=0.0, neon=None, wobble=0.0, step=1, ink=None)
_PAL_CACHE = {}
def pal(h):
    f = STYLE.get("bgmap")
    if not f: return h
    k = (STYLE["name"], h)
    if k not in _PAL_CACHE: _PAL_CACHE[k] = f(h)
    return _PAL_CACHE[k]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def lerp(a, b, x): return a + (b - a) * x
def seg(t, a, b): return clamp((t - a) / (b - a)) if b != a else (1.0 if t >= a else 0.0)
def eio(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
def back(x):
    x = clamp(x); c1 = 1.9; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def pop(t, t0, d=0.35): return back(seg(t, t0, t0 + d)) if t >= t0 else 0.0

def src(c, col, a=None):
    r, g, b, aa = hexc(col) if isinstance(col, str) else col
    c.set_source_rgba(r, g, b, aa if a is None else a)

def rrect(c, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    c.new_sub_path()
    c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    c.close_path()

def fill_rr(c, x, y, w, h, r, col, a=None):
    rrect(c, x, y, w, h, r); src(c, col, a); c.fill()

def text(c, s, x, y, size, col="#ffffff", font=BLACK, anchor="c", a=None, track=0):
    c.select_font_face(font, 0, 0); c.set_font_size(size)
    ext = c.text_extents(s)
    w = ext.x_advance + track * max(0, len(s) - 1)
    if anchor == "c": x0 = x - w / 2
    elif anchor == "r": x0 = x - w
    else: x0 = x
    src(c, col, a)
    if track:
        cx = x0
        for ch in s:
            c.move_to(cx, y); c.show_text(ch); cx += c.text_extents(ch).x_advance + track
        c.new_path()
    else:
        c.move_to(x0, y); c.show_text(s)
    c.new_path()
    return w

def text_w(c, s, size, font=BLACK):
    c.select_font_face(font, 0, 0); c.set_font_size(size); return c.text_extents(s).x_advance

# ---------- background ----------
STARS = [(random.Random(i).random() * W, random.Random(i * 7 + 3).random() * 760, random.Random(i * 13).random()) for i in range(90)]

def sky(c, t=0, dark=0.0):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *hexc(pal("#0a1020"))[:3]); g.add_color_stop_rgb(0.62, *hexc(pal("#141d33"))[:3]); g.add_color_stop_rgb(1, *hexc(pal("#0b0f1a"))[:3])
    c.set_source(g); c.paint()
    for (x, y, k) in STARS:
        a = 0.25 + 0.35 * (0.5 + 0.5 * math.sin(t * 1.3 + k * 20))
        src(c, pal("#ffffff"), a * (1 - dark)); c.arc(x, y, 1.1 if k > .5 else 0.8, 0, 2 * math.pi); c.fill()

def ground(c, y=820):
    g = cairo.LinearGradient(0, y, 0, H)
    g.add_color_stop_rgb(0, *hexc(pal("#10151f"))[:3]); g.add_color_stop_rgb(1, *hexc(pal("#07090f"))[:3])
    c.set_source(g); c.rectangle(0, y, W, H - y); c.fill()
    src(c, pal("#2a3550")); c.rectangle(0, y, W, 3); c.fill()

def vignette(c, k=0.55):
    g = cairo.RadialGradient(W / 2, 520, 200, W / 2, 560, 900)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, k)
    c.set_source(g); c.paint()

def darken(c, a):
    if a > 0: c.set_source_rgba(0.02, 0.03, 0.06, a); c.paint()

# ---------- UI overlays ----------
def sticky(c, s, x, y, t, t0, size=30, num=None, sub=None, col="#f1e8d0", tilt=-2):
    k = pop(t, t0)
    if k <= 0: return
    c.save(); c.translate(x, y); c.rotate(math.radians(tilt)); c.scale(k, k)
    full = (num + " " if num else "") + s
    w = text_w(c, full, size) + 40; h = size + 26 + (22 if sub else 0)
    src(c, "#000000", 0.35); c.rectangle(-w / 2 + 4, -h / 2 + 5, w, h); c.fill()
    src(c, col); c.rectangle(-w / 2, -h / 2, w, h); c.fill()
    by = -h / 2 + 13 + size * 0.78
    if num:
        nw = text_w(c, num + " ", size)
        text(c, num, -w / 2 + 20, by, size, C["red"], anchor="l")
        text(c, s, -w / 2 + 20 + nw, by, size, C["ink"], anchor="l")
    else:
        text(c, s, 0, by, size, C["ink"])
    if sub: text(c, sub, 0, by + 24, 15, "#555555", font=XB)
    c.restore()

def chip(c, s, x, y, t, t0, col="red", size=17, fg="#ffffff", t1=None, font=None):
    font = font or (CJK if any("\u4e00" <= ch <= "\u9fff" for ch in s) else BLACK)
    k = pop(t, t0, 0.3)
    if k <= 0: return
    a = 1.0
    if t1 is not None: a = 1 - seg(t, t1, t1 + 0.25)
    if a <= 0: return
    c.save(); c.translate(x, y); c.scale(k, k)
    w = text_w(c, s, size, font) + 30; h = size + 16
    fill_rr(c, -w / 2, -h / 2, w, h, h / 2, C.get(col, col), a)
    text(c, s, 0, size * 0.36, size, fg, font=font, a=a)
    c.restore()

def label(c, s, x, y, t, t0, size=18, col="#ffffff", a=1.0, font=None):
    k = seg(t, t0, t0 + 0.3)
    if k <= 0: return
    font = font or (CJK if any("\u4e00" <= ch <= "\u9fff" for ch in s) else BLACK)
    text(c, s, x, y, size, col, font=font, a=k * a)

def counter(c, x, y, t, t0, title, value, col="grn", w=190, h=74, sub=None):
    k = pop(t, t0, 0.3)
    if k <= 0: return
    c.save(); c.translate(x, y); c.scale(k, k)
    fill_rr(c, -w / 2, -h / 2, w, h, 10, "#0b1220", 0.92)
    rrect(c, -w / 2, -h / 2, w, h, 10); src(c, C[col]); c.set_line_width(2.5); c.stroke()
    text(c, title, 0, -h / 2 + 18, 12, C[col], font=XB, track=1)
    text(c, value, 0, h / 2 - 14, 34, C[col])
    c.restore()

def bubble(c, s, x, y, t, t0, size=20, col="#ffffff", fg="#111111", t1=None, tail=1):
    k = pop(t, t0, 0.3)
    if k <= 0: return
    a = 1.0 if t1 is None else 1 - seg(t, t1, t1 + 0.2)
    if a <= 0: return
    c.save(); c.translate(x, y); c.scale(k, k)
    w = text_w(c, s, size) + 28; h = size + 20
    fill_rr(c, -w / 2, -h, w, h, 12, col, a)
    src(c, col, a); c.move_to(-8 * tail, -1); c.line_to(6 * tail, -1); c.line_to(-4 * tail, 12); c.close_path(); c.fill()
    text(c, s, 0, -h / 2 + size * 0.36, size, fg, a=a)
    c.restore()

def stamp(c, s, x, y, t, t0, size=64, col="red", rot=-8):
    if t < t0: return
    x0 = seg(t, t0, t0 + 0.18); k = lerp(1.8, 1.0, eout(x0)); a = x0
    c.save(); c.translate(x, y); c.rotate(math.radians(rot)); c.scale(k, k)
    w = text_w(c, s, size) + 40; h = size + 24
    rrect(c, -w / 2, -h / 2, w, h, 8); src(c, C[col], a); c.set_line_width(6); c.stroke()
    text(c, s, 0, size * 0.36, size, C[col], a=a)
    c.restore()

def people_row(c, x, y, n, crossed, t, t0, size=26, gap=34, col="#ffffff"):
    total = (n - 1) * gap
    for i in range(n):
        k = pop(t, t0 + i * 0.05, 0.25)
        if k <= 0: continue
        px = x - total / 2 + i * gap
        dead = i >= n - crossed[0] and t >= crossed[1] if crossed else False
        cc = C["dim"] if dead else col
        c.save(); c.translate(px, y); c.scale(k, k)
        src(c, cc); c.arc(0, -size * 0.75, size * 0.22, 0, 2 * math.pi); c.fill()
        rrect(c, -size * 0.28, -size * 0.5, size * 0.56, size * 0.55, size * 0.18); c.fill()
        if dead:
            src(c, C["red"]); c.set_line_width(3)
            c.move_to(-12, -26); c.line_to(12, 2); c.move_to(12, -26); c.line_to(-12, 2); c.stroke()
        c.restore()

def clockchip(c, s, x, y, t, t0, col="yel"):
    k = pop(t, t0, 0.3)
    if k <= 0: return
    c.save(); c.translate(x, y); c.scale(k, k)
    w, h = 150, 54
    fill_rr(c, -w / 2, -h / 2, w, h, 10, "#0b1220", 0.92)
    rrect(c, -w / 2, -h / 2, w, h, 10); src(c, C[col]); c.set_line_width(2.5); c.stroke()
    text(c, s, 0, 13, 32, C[col])
    c.restore()

# ---------- props ----------
def portion(c, x, y, s=1.0, col="#e9e4d8", a=1.0):
    """cup-noodle style portion, bottom center x,y"""
    c.save(); c.translate(x, y); c.scale(s, s)
    src(c, col, a); c.move_to(-14, -34); c.line_to(14, -34); c.line_to(10, 0); c.line_to(-10, 0); c.close_path(); c.fill()
    src(c, pal("#e5484d"), a); c.rectangle(-13, -26, 26, 9); c.fill()
    src(c, pal("#cfc6b0"), a); c.rectangle(-16, -37, 32, 4); c.fill()
    c.restore()

def wrapper(c, x, y, s=1.0, rot=0, a=1.0):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    src(c, pal("#e5484d"), a); c.move_to(-16, -6); c.line_to(14, -9); c.line_to(17, 5); c.line_to(-12, 8); c.close_path(); c.fill()
    src(c, pal("#f1e8d0"), a); c.rectangle(-6, -4, 10, 6); c.fill()
    c.restore()

def padlock(c, x, y, s=1.0, closed=1.0, col="#f5c542"):
    c.save(); c.translate(x, y); c.scale(s, s)
    src(c, col); c.set_line_width(5); c.arc(0, -14 - (1 - closed) * 10, 11, math.pi, 2 * math.pi); c.stroke()
    c.move_to(-11, -14 - (1 - closed) * 10); c.line_to(-11, -14); c.stroke()
    fill_rr(c, -16, -16, 32, 26, 5, col)
    src(c, pal("#1b1b1f")); c.arc(0, -5, 3.5, 0, 2 * math.pi); c.fill(); c.rectangle(-1.5, -5, 3, 8); c.fill()
    c.restore()

def window(c, x, y, w, h, lit=0.0, frame=None):
    frame = frame or pal("#2c3754")
    src(c, C["win"]); c.rectangle(x, y, w, h); c.fill()
    if lit > 0:
        g = cairo.LinearGradient(x, y, x, y + h)
        g.add_color_stop_rgba(0, 0.98, 0.80, 0.38, lit); g.add_color_stop_rgba(1, 0.92, 0.65, 0.25, lit)
        c.set_source(g); c.rectangle(x, y, w, h); c.fill()
    src(c, frame); c.set_line_width(2); c.rectangle(x, y, w, h); c.stroke()
    c.move_to(x + w / 2, y); c.line_to(x + w / 2, y + h); c.stroke()

def moon(c, x, y, r=26):
    g = cairo.RadialGradient(x, y, r * 0.5, x, y, r * 4)
    g.add_color_stop_rgba(0, 0.95, 0.92, 0.8, 0.18); g.add_color_stop_rgba(1, 0.95, 0.92, 0.8, 0)
    c.set_source(g); c.arc(x, y, r * 4, 0, 2 * math.pi); c.fill()
    src(c, pal("#f3ecd6")); c.arc(x, y, r, 0, 2 * math.pi); c.fill()

def glow(c, x, y, r, col=(1, 0.85, 0.45), a=0.5):
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, *col, a); g.add_color_stop_rgba(1, *col, 0)
    c.set_source(g); c.arc(x, y, r, 0, 2 * math.pi); c.fill()

# ---------- building (side cross-section) ----------
# world coords: ground y=0, floors upward. Block B left, hall center, block A right
FH = 100
BX = (-340, -70); HX = (-70, 70); AX = (70, 340)

def building(c, t=0, lit_fn=None, cut=False, highlight=None, sealed=0.0, door_red=0.0, labels=True):
    """cut=True shows interior floor slabs; highlight=(block, floor, a)"""
    for (x0, x1), blk in ((BX, "Б"), (AX, "А")):
        src(c, C["bld"]); c.rectangle(x0, -6 * FH, x1 - x0, 6 * FH); c.fill()
        src(c, C["edge"]); c.set_line_width(3); c.rectangle(x0, -6 * FH, x1 - x0, 6 * FH); c.stroke()
        for f in range(1, 7):
            yb = -(f - 1) * FH
            if cut:
                src(c, C["edge"]); c.rectangle(x0, yb - 4, x1 - x0, 4); c.fill()
            for i in range(4):
                wx = x0 + 18 + i * (x1 - x0 - 36) / 4 + 6
                ww = (x1 - x0 - 36) / 4 - 12
                lit = lit_fn(blk, f, i) if lit_fn else 0.0
                window(c, wx, yb - FH + 26, ww, 46, lit)
        # roof
        src(c, C["bld2"]); c.rectangle(x0 - 8, -6 * FH - 12, x1 - x0 + 16, 12); c.fill()
        if labels:
            text(c, "БЛОК " + blk, (x0 + x1) / 2, -6 * FH - 26, 20, C["grey"])
    # hall
    src(c, C["bld2"]); c.rectangle(HX[0], -FH * 1.2, HX[1] - HX[0], FH * 1.2); c.fill()
    src(c, C["edge"]); c.set_line_width(3); c.rectangle(HX[0], -FH * 1.2, HX[1] - HX[0], FH * 1.2); c.stroke()
    # door
    dc = pal("#3a4a6a") if door_red <= 0 else None
    src(c, pal("#344260")); c.rectangle(-26, -78, 52, 78); c.fill()
    if door_red > 0:
        src(c, C["red"], door_red * (0.6 + 0.4 * math.sin(t * 6))); c.rectangle(-26, -78, 52, 78); c.fill()
    src(c, C["edge"]); c.set_line_width(2); c.rectangle(-26, -78, 52, 78); c.stroke(); c.move_to(0, -78); c.line_to(0, 0); c.stroke()
    if labels: text(c, "ХОЛЛ", 0, -FH * 1.2 - 12, 16, C["grey"])
    if sealed > 0:
        tape(c, -40, -70, 40, -10, sealed); tape(c, 40, -70, -40, -10, sealed)
    if highlight:
        blk, f, a = highlight
        x0, x1 = (AX if blk == "А" else BX)
        yb = -(f - 1) * FH
        src(c, C["yel"], a); c.set_line_width(4); c.rectangle(x0 + 3, yb - FH + 3, x1 - x0 - 6, FH - 6); c.stroke()

def tape(c, x0, y0, x1, y1, k=1.0):
    k = clamp(k); x1 = lerp(x0, x1, k); y1 = lerp(y0, y1, k)
    ang = math.atan2(y1 - y0, x1 - x0); L = math.hypot(x1 - x0, y1 - y0)
    c.save(); c.translate(x0, y0); c.rotate(ang)
    src(c, pal("#f5c542")); c.rectangle(0, -7, L, 14); c.fill()
    src(c, pal("#1b1b1f"))
    i = 0
    while i * 18 < L:
        c.move_to(i * 18, -7); c.line_to(i * 18 + 9, -7); c.line_to(min(i * 18 + 2, L), 7); c.line_to(max(i * 18 - 7, 0), 7); c.close_path(); c.fill(); i += 1
    c.restore()

def cam(c, cx, cy, s, sy=470):
    c.translate(W / 2, sy); c.scale(s, s); c.translate(-cx, -cy)

# ---------- rooms (screen coords, stage) ----------
FLOOR_Y = 800

def room_bg(c, kind, t=0, dark=0.0, moonlight=False):
    src(c, C["wall"]); c.rectangle(0, 0, W, FLOOR_Y); c.fill()
    # wall stripe
    src(c, C["wall2"]); c.rectangle(0, FLOOR_Y - 160, W, 160); c.fill()
    src(c, pal("#2a3550")); c.rectangle(0, FLOOR_Y - 162, W, 3); c.fill()
    src(c, C["floor"]); c.rectangle(0, FLOOR_Y, W, H - FLOOR_Y); c.fill()
    src(c, pal("#2a3550")); c.rectangle(0, FLOOR_Y, W, 4); c.fill()
    if kind == "kitchen":
        # window
        window(c, 470, 250, 170, 150, 0.0)
        if moonlight: glow(c, 555, 325, 220, (0.7, 0.8, 1.0), 0.18)
        # counter
        src(c, pal("#2a3550")); c.rectangle(30, 560, 380, 240); c.fill()
        src(c, pal("#38456a")); c.rectangle(24, 548, 392, 16); c.fill()
        for i in range(3):
            src(c, pal("#222b44")); c.rectangle(44 + i * 124, 590, 108, 190); c.fill()
            src(c, pal("#56648a")); c.rectangle(84 + i * 124, 600, 28, 5); c.fill()
        # stove
        src(c, pal("#121826")); c.arc(110, 540, 22, math.pi, 2 * math.pi); c.fill(); c.arc(190, 540, 22, math.pi, 2 * math.pi); c.fill()
        # upper cabinets
        src(c, pal("#232c46")); c.rectangle(30, 180, 380, 150); c.fill()
        src(c, pal("#2f3a5a")); c.set_line_width(3)
        for i in range(3): c.rectangle(34 + i * 126, 184, 120, 142); c.stroke()
        text(c, tr("КУХНЯ", "KITCHEN"), 120, 140, 22, C["dim"])
    elif kind == "dorm":
        window(c, 290, 220, 150, 140, 0.0)
        # beds
        for bx in (40, 470):
            src(c, pal("#2a3550")); c.rectangle(bx, 640, 210, 40); c.fill()
            src(c, pal("#3b4a72")); c.rectangle(bx, 610, 210, 34); c.fill()
            src(c, pal("#dfe3ee")); fill_rr(c, bx + 8, 598, 60, 22, 8, pal("#c8cfdf"))
            src(c, pal("#2a3550")); c.rectangle(bx, 680, 12, 120); c.fill(); c.rectangle(bx + 198, 680, 12, 120); c.fill()
        # desk
        src(c, pal("#2a3550")); c.rectangle(290, 600, 150, 14); c.fill(); c.rectangle(300, 614, 10, 186); c.fill(); c.rectangle(420, 614, 10, 186); c.fill()
    elif kind == "laundry":
        for i in range(4):
            x = 40 + i * 165
            fill_rr(c, x, 560, 140, 240, 10, pal("#d9dde8"))
            src(c, pal("#9aa3b8")); c.rectangle(x, 560, 140, 40); c.fill()
            src(c, pal("#1e2740")); c.arc(x + 70, 690, 46, 0, 2 * math.pi); c.fill()
            src(c, pal("#3d6fbf"), 0.6); c.arc(x + 70, 690, 36, 0, 2 * math.pi); c.fill()
        text(c, tr("ПРАЧЕЧНАЯ", "LAUNDRY"), W / 2, 140, 22, C["dim"])
        # ceiling panels
        src(c, pal("#232c46"))
        for i in range(5): c.rectangle(20 + i * 140, 30, 130, 60); c.fill()
    elif kind == "corridor":
        for i in range(4):
            x = 40 + i * 175
            src(c, pal("#2b3550")); c.rectangle(x, 470, 110, 330); c.fill()
            src(c, pal("#3a4770")); c.set_line_width(3); c.rectangle(x, 470, 110, 330); c.stroke()
            src(c, C["yel"]); c.arc(x + 92, 640, 5, 0, 2 * math.pi); c.fill()
        # ceiling lamps off
        for i in range(3):
            src(c, pal("#2a3550")); c.rectangle(100 + i * 220, 60, 90, 10); c.fill()
    elif kind == "stairs":
        src(c, pal("#232c46"))
        for i in range(10):
            c.rectangle(40 + i * 64, FLOOR_Y - (i + 1) * 54, 64, (i + 1) * 54); c.fill()
        src(c, pal("#38456a")); c.set_line_width(4)
        c.move_to(40, FLOOR_Y - 120); c.line_to(680, FLOOR_Y - 120 - 540); c.stroke()
        src(c, C["grn"], 0.8); fill_rr(c, 560, 120, 110, 40, 6, C["grn"]); text(c, "EXIT", 615, 148, 22, pal("#ffffff"))
    elif kind == "hall":
        src(c, pal("#232c46")); c.rectangle(0, 0, W, 90); c.fill()
        for x in (120, 600):
            src(c, pal("#263252")); c.rectangle(x - 22, 90, 44, FLOOR_Y - 90); c.fill()
        src(c, pal("#344260")); c.rectangle(280, 430, 160, 370); c.fill()
        src(c, pal("#4a5a82")); c.set_line_width(4); c.rectangle(280, 430, 160, 370); c.stroke(); c.move_to(360, 430); c.line_to(360, 800); c.stroke()
        text(c, tr("← Б", "← B"), 70, 380, 26, C["dim"]); text(c, tr("А →", "A →"), 650, 380, 26, C["dim"])
    if dark > 0: darken(c, dark)

def cabinet(c, x, y, t, t_close=None, items=0, lock=True, open_=0.0, w=200, h=230):
    """standing cabinet; x,y bottom-left"""
    src(c, pal("#2f3a5a")); c.rectangle(x, y - h, w, h); c.fill()
    src(c, pal("#18203a")); c.rectangle(x + 10, y - h + 10, w - 20, h - 20); c.fill()
    # shelves with portions
    n = 0
    for r in range(3):
        sy = y - h + 10 + (r + 1) * (h - 20) / 3
        src(c, pal("#3c4a72")); c.rectangle(x + 10, sy - 4, w - 20, 4); c.fill()
        for i in range(5):
            if n < items: portion(c, x + 32 + i * 34, sy - 4, 0.75)
            n += 1
    # doors
    d = 1 - open_
    if d > 0:
        for sgn in (0, 1):
            dw = (w / 2 - 6) * d
            dx = x + 6 if sgn == 0 else x + w - 6 - dw
            src(c, pal("#3a4870")); c.rectangle(dx, y - h + 6, dw, h - 12); c.fill()
            src(c, pal("#4c5d8e")); c.set_line_width(2); c.rectangle(dx, y - h + 6, dw, h - 12); c.stroke()
        if lock and d > 0.9:
            k = 1.0 if t_close is None else eout(seg(t, t_close, t_close + 0.3))
            padlock(c, x + w / 2, y - h / 2 + 20, 1.2, k)

def bed_side(c, x, y, w=260):
    src(c, pal("#2a3550")); c.rectangle(x, y - 120, w, 34); c.fill()
    src(c, pal("#3b4a72")); c.rectangle(x, y - 150, w, 34); c.fill()
    fill_rr(c, x + 8, y - 168, 66, 24, 8, pal("#c8cfdf"))
    src(c, pal("#2a3550")); c.rectangle(x, y - 86, 12, 86); c.fill(); c.rectangle(x + w - 12, y - 86, 12, 86); c.fill()
    src(c, pal("#05070c"), 0.6); c.rectangle(x + 12, y - 86, w - 24, 86); c.fill()

def footprint(c, x, y, s, rot, col, a=1.0):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    src(c, col, a); c.save(); c.scale(1, 1.9); c.arc(0, 0, 9, 0, 2 * math.pi); c.restore(); c.fill()
    c.arc(0, 22, 7, 0, 2 * math.pi); c.fill()
    c.restore()

def notice(c, x, y, s, t, small_glow=0.0, title=None, big=None, line=None, small=None):
    """A posted notice. Defaults: quarantine notice in the project language; pass title/big/line/small to change."""
    title = title or tr("КАРАНТИН", "QUARANTINE"); big = big or tr("10 ДНЕЙ", "10 DAYS")
    line = line or tr("ДОСТАВКИ ЗАПРЕЩЕНЫ", "NO DELIVERIES"); small = small or "*期限可能延长"
    c.save(); c.translate(x, y); c.scale(s, s)
    src(c, pal("#000000"), 0.4); c.rectangle(-150 + 6, -200 + 8, 300, 400); c.fill()
    src(c, pal("#f4f1e8")); c.rectangle(-150, -200, 300, 400); c.fill()
    src(c, pal("#c4312f")); c.rectangle(-150, -200, 300, 12); c.fill()
    text(c, "隔离通知", 0, -140, 44, pal("#c4312f"), font=CJK)
    text(c, title, 0, -92, 30, pal("#1b1b1f"))
    text(c, big, 0, -50, 46, pal("#c4312f"))
    src(c, pal("#b9b4a6"))
    for i in range(5): c.rectangle(-115, -10 + i * 22, 230 - (i % 2) * 40, 8); c.fill()
    text(c, line, 0, 118, 16, pal("#1b1b1f"), font=XB)
    if small_glow > 0:
        glow(c, 60, 166, 90, (1, 0.8, 0.3), 0.35 * small_glow)
    text(c, small, 60, 170, 13, pal("#555555"), font=CJK)
    src(c, pal("#c4312f")); c.arc(100, 140, 20, 0, 2 * math.pi); c.set_line_width(3); c.stroke()
    c.restore()

