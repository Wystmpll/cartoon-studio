"""Word-by-word karaoke captions. Spoken words light up; key words get accent colours."""
import re
from engine import *

CAP = {}   # current caption style (set by render.load_project)
KEY_RED = set()   # filled by project: danger words (upper-case, without punctuation)
KEY_YEL = set()   # names, numbers, key nouns

def set_keywords(red=(), yel=()):
    KEY_RED.clear(); KEY_YEL.clear()
    KEY_RED.update(w.upper() for w in red); KEY_YEL.update(w.upper() for w in yel)

def norm(w, upper=True):
    w = re.sub(r"[«»\"]", "", w)
    return w.upper() if upper else w

def _bare(w):
    return re.sub(r"[^\w\-]", "", w.upper())

def word_col(w, cap):
    b = _bare(w)
    if b in KEY_RED or any(b.startswith(k) and len(k) >= 5 for k in KEY_RED): return cap.get("red") or C["red"]
    if b in KEY_YEL or any(b.startswith(k) and len(k) >= 4 for k in KEY_YEL): return cap.get("yel") or C["yel"]
    if re.search(r"\d", b): return cap.get("yel") or C["yel"]
    return cap["spoken"]

def chunks(line, maxc=15, maxw=3):
    ws = line["words"]; out = []; cur = []
    for w in ws:
        cur.append(w)
        txt = " ".join(x["w"] for x in cur)
        if w["w"].endswith((".", "?", "!", ",", ":", "»")) or len(txt) >= maxc or len(cur) >= maxw:
            out.append(cur); cur = []
    if cur: out.append(cur)
    return out

def build_chunks(timing):
    allc = []
    for sc in timing["scenes"]:
        for ln in sc["lines"]:
            allc.extend(chunks(ln))
    for i, ch in enumerate(allc):
        nxt = allc[i + 1][0]["s"] if i + 1 < len(allc) else ch[-1]["e"] + 0.4
        end = min(nxt, ch[-1]["e"] + 0.9)
        for w in ch: w["_cend"] = end
    return allc

def _box(c, kind, x, y, w, h, cap):
    if kind == "comic":
        src(c, "#111111"); c.rectangle(x - 4, y - 4, w + 8, h + 8); c.fill(); src(c, cap.get("box_col") or "#ffe14a"); c.rectangle(x, y, w, h); c.fill()
    elif kind == "intertitle":
        src(c, "#0a0a0a"); c.rectangle(x - 30, y - 18, w + 60, h + 36); c.fill()
        src(c, "#e8e2d0"); c.set_line_width(3); c.rectangle(x - 22, y - 10, w + 44, h + 20); c.stroke()
    elif kind == "type":
        src(c, "#f1ead6"); c.rectangle(x - 10, y - 6, w + 20, h + 12); c.fill()
    elif kind == "strip":
        src(c, "#000000", 0.25); c.rectangle(x - 10, y - 2, w + 20, h + 10); c.fill(); src(c, "#f6f0e2"); c.rectangle(x - 14, y - 8, w + 20, h + 10); c.fill()
    elif kind == "pixel":
        src(c, "#000000", 0.8); c.rectangle(x - 12, y - 8, w + 24, h + 16); c.fill(); src(c, "#ffffff"); c.set_line_width(4); c.rectangle(x - 12, y - 8, w + 24, h + 16); c.stroke()
    elif kind == "marker":
        src(c, "#ffe14a", 0.85); c.rectangle(x - 8, y + h * 0.35, w + 16, h * 0.62); c.fill()

def draw_captions(c, T, allc, cap):
    y = cap["y"]
    for ch in allc:
        s0 = ch[0]["s"]; e = ch[0]["_cend"]
        if not (s0 - 0.02 <= T < e): continue
        size = cap["size"]; font = cap["font"]
        words = [norm(w["w"], cap["upper"]) for w in ch]
        sp = text_w(c, " ", size, font); widths = [text_w(c, w, size, font) for w in words]
        total = sum(widths) + sp * (len(words) - 1)
        if total > W - 70:
            size = int(size * (W - 70) / total); sp = text_w(c, " ", size, font); widths = [text_w(c, w, size, font) for w in words]
            total = sum(widths) + sp * (len(words) - 1)
        x = W / 2 - total / 2
        k = eout(seg(T, s0, s0 + 0.12)); yy = y + (1 - k) * 10
        boxed = cap.get("box")
        if boxed:
            _box(c, boxed, x - 14, yy - size * 0.95, total + 28, size * 1.3, cap)
        fg_dark = boxed in ("comic", "type", "strip", "marker") and cap["spoken"] in ("#ffffff",)
        for w, ww, wd in zip(ch, words, widths):
            spoken = T >= w["s"] - 0.03
            col = word_col(w["w"], cap) if spoken else cap["spoken"]
            if fg_dark and col == "#ffffff": col = "#111111"
            if boxed in ("comic", "type", "strip") and col == C["yel"]: col = "#c4312f" if boxed != "comic" else "#1a4fd8"
            a = 1.0 if spoken else cap["future_a"]
            if a <= 0: x += wd + sp; continue
            if cap.get("shadow"):
                src(c, "#000000", 0.55 * a); c.select_font_face(font, 0, 0); c.set_font_size(size); c.move_to(x + 2, yy + 4); c.show_text(ww); c.new_path()
            text(c, ww, x, yy, size, col, font=font, anchor="l", a=a)
            x += wd + sp
        return
