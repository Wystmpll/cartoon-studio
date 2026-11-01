"""18 visual styles. A style = character knobs (engine.STYLE) + background re-colouring (pal) +
per-frame post-processing (numpy) + caption look. apply(name) switches everything globally."""
import colorsys, math, random
import numpy as np
from PIL import Image, ImageFilter
import engine
from engine import C, W, H

def _hls(h):
    r, g, b, _ = engine.hexc(h); return colorsys.rgb_to_hls(r, g, b)
def _hex(r, g, b):
    return "#%02x%02x%02x" % tuple(int(max(0, min(1, v)) * 255) for v in (r, g, b))

def remap(light=None, sat=1.0, hue_to=None, hue_k=0.0, lmul=1.0):
    """Background recolour: light=(a,b) -> L' = a + b*L ; or lmul scales L."""
    def f(h):
        hh, l, s = _hls(h)
        if light: l = light[0] + light[1] * l
        else: l = l * lmul
        s = s * sat
        if hue_to is not None:
            d = ((hue_to - hh + 0.5) % 1.0) - 0.5; hh = (hh + d * hue_k) % 1.0
        return _hex(*colorsys.hls_to_rgb(hh, max(0, min(1, l)), max(0, min(1, s))))
    return f

# ---------------- textures (cached) ----------------
_TEX = {}
def tex(kind):
    if kind in _TEX: return _TEX[kind]
    rng = np.random.default_rng(7)
    if kind == "grain":
        t = rng.normal(0, 1, (H + 64, W + 64)).astype(np.float32)
    elif kind == "paper":
        n = rng.normal(0, 1, (H // 4, W // 4)).astype(np.float32)
        im = Image.fromarray(((n - n.min()) / (np.ptp(n) + 1e-6) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(2))
        fine = rng.normal(0, 1, (H, W)).astype(np.float32)
        t = 0.93 + 0.07 * (np.asarray(im, np.float32) / 255.0) + 0.015 * fine
    elif kind == "halftone":
        yy, xx = np.mgrid[0:H, 0:W]
        p = 9.0
        d = np.hypot((xx % p) - p / 2, (yy % p) - p / 2) / (p / 2)
        t = d.astype(np.float32)   # 0 at dot centre .. ~1.4 corners
    elif kind == "lowpoly":
        img = Image.new("L", (W, H), 128)
        from PIL import ImageDraw
        dr = ImageDraw.Draw(img); r = random.Random(3); s = 90
        for y in range(-s, H + s, s):
            for x in range(-s, W + s, s):
                ox = (y // s) % 2 * s / 2
                a = (x + ox, y); b = (x + ox + s, y); c2 = (x + ox + s / 2, y + s); d2 = (x + ox - s / 2, y + s)
                dr.polygon([a, b, c2], fill=128 + r.randint(-14, 14)); dr.polygon([a, c2, d2], fill=128 + r.randint(-14, 14))
        t = np.asarray(img, np.float32) / 128.0
    elif kind == "gouache":
        n = rng.normal(0, 1, (H // 8, W // 8)).astype(np.float32)
        im = Image.fromarray(((n - n.min()) / (np.ptp(n) + 1e-6) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6))
        streak = np.tile(rng.normal(0, 1, (1, W)).astype(np.float32), (H, 1))
        t = 0.9 + 0.1 * (np.asarray(im, np.float32) / 255.0) + 0.012 * streak
    _TEX[kind] = t
    return t

# ---------------- post ops on BGRA uint8 arrays ----------------
def _rgb(a): return a[..., :3].astype(np.float32)
def _put(a, f): a[..., :3] = np.clip(f, 0, 255).astype(np.uint8)

def op_grain(a, fi, k=10):
    g = tex("grain"); ox, oy = (fi * 17) % 64, (fi * 29) % 64
    _put(a, _rgb(a) + g[oy:oy + H, ox:ox + W, None] * k)

def op_mul(a, kind, strength=1.0):
    t = tex(kind)
    _put(a, _rgb(a) * (1 + (t[..., None] - 1) * strength))

def op_gray(a, sepia=False, contrast=1.0, keep_red=False):
    f = _rgb(a); b, g, r = f[..., 0], f[..., 1], f[..., 2]
    y = 0.299 * r + 0.587 * g + 0.114 * b
    y = np.clip((y - 128) * contrast + 128, 0, 255)
    if sepia: out = np.stack([y * 0.78, y * 0.92, y * 1.05], -1)
    else: out = np.stack([y, y, y], -1)
    if keep_red:
        m = ((r > g * 1.45) & (r > b * 1.45) & (r > 90))[..., None]
        out = np.where(m, f, out)
    _put(a, out)

def op_desat(a, k=0.5, tint=(1, 1, 1)):
    f = _rgb(a); y = (0.299 * f[..., 2] + 0.587 * f[..., 1] + 0.114 * f[..., 0])[..., None]
    _put(a, (f * (1 - k) + y * k) * np.array(tint[::-1], np.float32))

def op_posterize(a, levels=6):
    f = _rgb(a); q = 255.0 / (levels - 1)
    _put(a, np.round(f / q) * q)

def op_pixel(a, factor=5):
    im = Image.frombuffer("RGBA", (W, H), a.tobytes(), "raw", "RGBA", 0, 1)
    small = im.resize((W // factor, H // factor), Image.BOX).resize((W, H), Image.NEAREST)
    a[...] = np.asarray(small)

def op_halftone(a, strength=0.35):
    t = tex("halftone"); f = _rgb(a)
    lum = (0.299 * f[..., 2] + 0.587 * f[..., 1] + 0.114 * f[..., 0]) / 255.0
    dot = (t < (1 - lum) * 1.2).astype(np.float32)
    _put(a, f * (1 - strength * dot[..., None]))

def op_bloom(a, k=0.5, radius=14, thr=150):
    f = _rgb(a)
    bright = np.clip(f - thr, 0, 255).astype(np.uint8)
    im = Image.fromarray(bright[..., ::-1].copy()).resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(radius / 4)).resize((W, H), Image.BILINEAR)
    _put(a, f + np.asarray(im, np.float32)[..., ::-1] * k * 2)

def op_blur(a, r=1.2):
    im = Image.fromarray(a[..., :3][..., ::-1].copy()).filter(ImageFilter.GaussianBlur(r))
    a[..., :3] = np.asarray(im)[..., ::-1]

def op_chroma(a, px=3):
    f = a.copy()
    a[..., 2] = np.roll(f[..., 2], px, axis=1); a[..., 0] = np.roll(f[..., 0], -px, axis=1)

def op_flicker(a, fi, k=0.08):
    r = random.Random(fi).uniform(1 - k, 1 + k * 0.3)
    _put(a, _rgb(a) * r)

def op_jitter(a, fi, px=2):
    r = random.Random(fi * 3)
    dx, dy = r.randint(-px, px), r.randint(-px, px)
    a[...] = np.roll(np.roll(a, dy, 0), dx, 1)

def op_contrast(a, k=1.15, bright=0):
    _put(a, (_rgb(a) - 128) * k + 128 + bright)

def op_glitch(a, fi):
    r = random.Random(fi)
    if r.random() < 0.06:
        y0 = r.randint(0, H - 80); h = r.randint(10, 60); dx = r.randint(-30, 30)
        a[y0:y0 + h] = np.roll(a[y0:y0 + h], dx, 1)
        op_chroma(a, 6)

def op_vignette(a, k=0.5):
    if "vig" not in _TEX:
        yy, xx = np.mgrid[0:H, 0:W]; d = np.hypot((xx - W / 2) / (W * 0.75), (yy - H * 0.42) / (H * 0.7))
        _TEX["vig"] = np.clip(1 - d ** 2.2, 0, 1).astype(np.float32)
    v = _TEX["vig"]
    _put(a, _rgb(a) * (1 - k + k * v)[..., None])

# ---------------- style catalog ----------------
DARK = None
S = {}
def style(key, ru, desc, knobs=None, bg=None, post=(), cap=None, vignette=0.35, accents=None, overlay=None):
    S[key] = dict(key=key, ru=ru, desc=desc, knobs=knobs or {}, bg=bg, post=post, cap=cap or {}, vignette=vignette,
                  accents=accents or {}, overlay=overlay)

CAP_DEFAULT = dict(font="Inter Black", size=50, upper=True, spoken="#ffffff", future_a=0.32, box=None, y=905,
                   shadow=True, red=None, yel=None, box_col=None, fg_box=None)

style("survival", "Ночной флэт (survival)", "Тёмно-синяя ночь, жёлтые и красные акценты, стикеры и таймеры. Напряжённые истории выживания.")
style("chibi", "Чиби-флэт", "Большие головы, яркая одежда, живая мимика. Комедия, повседневность, школьные истории.",
      knobs=dict(head_scale=1.28), bg=remap(lmul=1.25, sat=1.1))
style("anime", "Аниме", "Большие глаза с бликами, жёсткие тени, контуры, линии скорости, сиреневый закат. Драма, экшен, романтика.",
      knobs=dict(eye="anime", cel=1.0, outline=2.2, outline_col="#1a1030", head_scale=1.12), bg=remap(lmul=1.35, sat=1.25, hue_to=0.72, hue_k=0.35),
      post=(("bloom", 0.25),), cap=dict(spoken="#ffffff", shadow=True))
style("comic", "Комикс", "Толстые чёрные контуры, растровые точки, плакатные цвета, звуки «БАМ!». Экшен, пародия.",
      knobs=dict(outline=5.0, outline_col="#0a0a0a"), bg=remap(lmul=1.6, sat=1.4),
      post=(("posterize", 7), ("halftone", 0.28)), cap=dict(box="comic", upper=True, font="Inter Black", size=44, future_a=0.0), vignette=0.0)
style("papercut", "Бумажная аппликация", "Персонажи из вырезанной бумаги с тенью, дёрганая анимация, текстура картона. Сказки, детские истории.",
      knobs=dict(drop_shadow=10, step=2, outline=1.2, outline_col="#f4efe2"), bg=remap(light=(0.72, -0.5), sat=0.45, hue_to=0.09, hue_k=1.0),
      post=(("paper", 1.0),), cap=dict(box="strip", font="Inter ExtraBold", size=42, upper=False, spoken="#2a2018"), vignette=0.15)
style("pixel", "Пиксель-арт", "Крупные пиксели, ограниченная палитра, как в старых играх. Геймерские сюжеты.",
      knobs=dict(step=2), bg=remap(lmul=1.3, sat=1.2), post=(("pixel", 5), ("posterize", 6)),
      cap=dict(font="DejaVu Sans Mono", size=40, box="pixel", upper=True, future_a=0.0), vignette=0.0)
style("doodle", "Каракули в тетрадке", "Лист в клетку или линейку, чёрные контуры от руки, маркерные цвета, «кипящие» линии. Мемы, объяснения.",
      knobs=dict(outline=3.0, outline_col="#1a1a1a", eye="dot", head_scale=1.15, step=3, wobble=1.5), bg=remap(light=(0.98, -0.5), sat=0.4),
      post=(("mul_paper", 0.6),), cap=dict(font="Inter ExtraBold", size=46, upper=False, spoken="#151515", shadow=False, box="marker", yel="#1a4fd8"), vignette=0.0,
      overlay="notebook")
style("noir", "Нуар", "Чёрно-белое, жёсткий контраст, только красный остаётся цветным, зерно и дождь. Детектив, триллер.",
      knobs=dict(outline=1.5, outline_col="#000000"), post=(("gray_red", 1.35), ("grain", 14)),
      cap=dict(font="DejaVu Serif", size=46, upper=True, spoken="#f2f2f2"), vignette=0.6, overlay="rain")
style("isometric", "Изометрия", "Комнаты и здания как макет сверху под углом, маленькие человечки. Планы, «кто где был», ограбления.",
      knobs=dict(outline=1.2, outline_col="#141a2a", head_scale=1.15), bg=remap(lmul=1.4, sat=1.2), vignette=0.2)
style("retro30", "Ретро-мультфильм 1930-х", "Чёрно-белая плёнка, «пирожковые» глаза, зерно, дрожание кадра, титры на чёрных карточках.",
      knobs=dict(eye="pie", step=2, outline=2.0, outline_col="#000000"), post=(("gray_sepia", 1.25), ("grain", 22), ("flicker", 0.1), ("jitter", 2)),
      cap=dict(box="intertitle", font="DejaVu Serif", size=40, upper=False, future_a=0.0), vignette=0.75)
style("soviet", "Тёплая советская аппликация", "Гуашевые текстуры, тёплые охра и бирюза, мягкие тени, неспешный ритм. Ностальгия, добрые истории.",
      knobs=dict(drop_shadow=5, step=2, head_scale=1.05), bg=remap(light=(0.74, -0.55), sat=0.55, hue_to=0.1, hue_k=1.0),
      post=(("gouache", 1.0), ("desat", 0.15)), cap=dict(font="DejaVu Serif", size=44, upper=False, spoken="#3a2414", shadow=False, yel="#9a2a1a", future_a=0.28), vignette=0.3)
style("neon", "Неон-киберпанк", "Тёмный город, светящиеся контуры, сияние, цифровые глитчи. Фантастика, хакеры, ночные гонки.",
      knobs=dict(neon="#29f0ff", outline=2.4), bg=remap(lmul=0.75, sat=1.6, hue_to=0.78, hue_k=0.6),
      post=(("bloom", 0.8), ("glitch", 1)), cap=dict(spoken="#ff4fd8", shadow=True), vignette=0.45)
style("watercolor", "Акварель", "Мягкие размытые цвета, бумага, нежный свет. Романтика, грусть, воспоминания.",
      knobs=dict(head_scale=1.08), bg=remap(light=(0.93, -0.45), sat=0.55, hue_to=0.05, hue_k=0.2),
      post=(("blur", 1.3), ("paper", 1.0)), cap=dict(font="Inter ExtraBold", size=44, upper=False, spoken="#3a2a22", shadow=False, future_a=0.25, yel="#1a4fd8"), vignette=0.25)
style("clay", "Пластилин", "Объёмные мягкие формы с бликом и тенью, анимация «по кадрам». Комедия, детские и абсурдные истории.",
      knobs=dict(clay=1.0, drop_shadow=6, step=2, head_scale=1.12), bg=remap(light=(0.62, -0.3), sat=0.6, hue_to=0.06, hue_k=0.85),
      post=(("blur", 0.6),), vignette=0.35)
style("explainer", "Объяснялка-схема", "Светлый фон, стрелки, графики, иконки, цифры. Как что-то устроено, факты, инструкции.",
      knobs=dict(head_scale=1.1), bg=remap(light=(0.99, -0.3), sat=0.35),
      cap=dict(spoken="#111111", shadow=False, box="marker", upper=False, font="Inter Black", size=46, yel="#1a4fd8"), vignette=0.0)
style("horror", "Хоррор-скетч", "Обесцвеченный, дрожащие контуры, красные акценты, зерно, мерцание. Ужасы, крипипасты.",
      knobs=dict(outline=2.0, outline_col="#050505", wobble=2.5, step=2), bg=remap(lmul=0.8, sat=0.4, hue_to=0.35, hue_k=0.2),
      post=(("desat", 0.55), ("grain", 18), ("chroma", 2), ("flicker", 0.12)), cap=dict(spoken="#f0f0f0", red="#ff2b2b"), vignette=0.7)
style("lowpoly", "Псевдо-3D (low-poly)", "Гранёные треугольные поверхности, объёмный свет. Игровая и технологичная подача.",
      knobs=dict(cel=0.8, outline=0.8, outline_col="#10131c"), bg=remap(lmul=1.25, sat=1.15), post=(("lowpoly", 1.0),), vignette=0.3)
style("truecrime", "True crime / доска улик", "Пробковая доска, фото-полароиды, красные нитки, вырезки, машинописные титры. Расследования, «кто это сделал».",
      knobs=dict(outline=1.0, outline_col="#2a2a2a"), post=(("desat", 0.2), ("grain", 8)),
      cap=dict(box="type", font="DejaVu Sans Mono", size=38, upper=True, future_a=0.0), vignette=0.45, overlay="cork")

ORDER = list(S)

def apply(key):
    st = S[key]
    engine.STYLE.clear()
    engine.STYLE.update(dict(name=key, bgmap=st["bg"], head_scale=1.0, eye="round", outline=0.0, outline_col="#111111",
                             drop_shadow=0.0, cel=0.0, clay=0.0, neon=None, wobble=0.0, step=1, ink=None))
    engine.STYLE.update(st["knobs"])
    engine._PAL_CACHE.clear()
    # background palette keys
    base = dict(bg1="#0b1120", bg2="#131c31", bld="#1a2338", bld2="#212b44", edge="#2c3754", win="#263049", wall="#182036", wall2="#1d2740",
                floor="#0d121e", dim="#4a5470", grey="#7d869c")
    for k, v in base.items(): C[k] = engine.pal(v)
    cap = dict(CAP_DEFAULT); cap.update(st["cap"])
    return dict(style=st, cap=cap)

def post_process(arr, t, fi, st):
    for name, k in st["post"]:
        if name == "grain": op_grain(arr, fi, k)
        elif name == "paper": op_mul(arr, "paper", k)
        elif name == "mul_paper": op_mul(arr, "paper", k)
        elif name == "gouache": op_mul(arr, "gouache", k)
        elif name == "lowpoly": op_mul(arr, "lowpoly", k * 0.9)
        elif name == "gray_red": op_gray(arr, contrast=k, keep_red=True)
        elif name == "gray_sepia": op_gray(arr, sepia=True, contrast=k)
        elif name == "desat": op_desat(arr, k)
        elif name == "posterize": op_posterize(arr, k)
        elif name == "pixel": op_pixel(arr, k)
        elif name == "halftone": op_halftone(arr, k)
        elif name == "bloom": op_bloom(arr, k)
        elif name == "blur": op_blur(arr, k)
        elif name == "chroma": op_chroma(arr, k)
        elif name == "flicker": op_flicker(arr, fi, k)
        elif name == "jitter": op_jitter(arr, fi, k)
        elif name == "glitch": op_glitch(arr, fi)
    if st["vignette"] > 0: op_vignette(arr, st["vignette"])
