# Writing scenes (scenes_p<N>.py)

```python
from world import *          # engine + chars + world helpers (W=720, H=1280, FPS=30, FLOOR_Y=800)

def hook(c, t, S):           # c = cairo context, t = seconds since scene start, S = scene helper
    street(c, t, night=True)
    person(c, "Нурали", 360, 820, 380, t, mood="scared", tag=True, tagt=0.3)
    chip(c, "ПОСЛЕДНИЙ АВТОБУС", W / 2, 110, t, S.w("автобус"), "red", 20)
    S.sfx("sting", S.L(1))

SCENES = dict(hook=hook)     # every scene id from script.PARTS[N] except "end" (end card is automatic)
```
Scene functions are pure functions of t: draw everything every frame, no state between frames (use `S.smooth` for
camera follow). Time anchors: `S.L(i)` start of line i, `S.Le(i)` its end, `S.w("слово", n=0)` start of the n-th word
starting with that text (case-insensitive, punctuation ignored; raises KeyError if absent — pick a word that exists
in that scene, beware prefixes: "нура" also matches "Нурали", use n=1), `S.dur` scene length, `S.sfx(name, at, vol)`.

## Frame layout (9:16, 720×1280)
- Illustration lives in y ≈ 0-820; floor line FLOOR_Y = 800. Captions are drawn at y≈905 automatically — keep faces
  and key text above ~850. Top band y 60-260 is for chips/stickers/counters (keep 2-3 max at once).
- Character size: H is the px height of a 185 cm person. Group shot 220-380, medium 420-640, close-up use
  `closeup2(c, name, t, Hh=860)` (head at y≈420). Name tags (`tag=True`) go above small characters, beside big ones.

## Characters — chars.person(c, name, x, y_feet, H, t, **kw)
look (-1..1 eyes), mood: n happy scared angry sad smug focus; mouth: talk shout laugh smile smirk o grit flat down;
walk=phase (e.g. t*1.6) and run=True; arms=(back, front) radians (0 down, 1.4 forward, 2.6 up); lean; shake (0-1);
alpha; sil=True silhouette; zombie=True green version; eyes_closed; cover_mouth; glow_face (phone light);
holding "phone" | "flashlight" | "radio"; tag/tagt (name label pops at tagt). Pose helpers: `sit`, `lying`,
`ear_phone`, `head_pos`. Crowds: `zombie(...)`, `crowd(c, t, n, x0, x1, y, H, seed, face, alert, depth, speed)`.

## Sets and props
Exteriors: `ext_dorm`, `building(cut=True, highlight=("А",2,1.0))` + `cam(c, cx, cy, scale, screen_y)`, `street`,
`forest`, `rooftop`, `sky`, `ground`, `moon`, `trees`, `lamp`, `heli`, `site_map(places, route)` (top-down map),
`campus_map` (NPU Chang'an preset). Interiors: `room(kind)` with roomA roomB hall hallglass teach corridor kitchen laundry
stairs dorm; `classroom`, `canteen`, `iso_room`+`iso_box`, `paper_bg("notebook"|"graph"|"cork")`.
Props: portion, wrapper, padlock, window, cabinet, bed_side, footprint, notice, tape, speaker, notes, heart.
UI: sticky (rules «1. ЗВУК»), chip, label, counter, clockchip, bubble, stamp, people_row, phone (group chat with
messages [(time, name, text)]), arrow, burst («БАМ!»). Composition: `panel` (split screen/comic panels), `polaroid`.
FX: fog, dust, rain, snow, fire, explosion, glow, light_cone, speed_lines, flash_red, handheld (camera shake),
darken, vignette. Timing/easing: seg, eout, eio, pop, lerp, clamp.
Colours: for new background drawing use `pal("#hex")` so styles can recolour it; UI accents via C["red"|"yel"|"grn"|"blu"|"dim"].

## SFX names
whoosh swoosh_up impact boom thud punch knock steps heartbeat glass door buzz typing pop click beep ding riser sting
scream groan crowd rotor splash alarm wind rain laugh_beep. Put 1-3 per scene on real events (door, hit, reveal).

## Lessons learned (pitfalls)
- Frame is cleared by the renderer, but a set that doesn't paint the area below the floor leaves it dark — fine.
- `c.scale(k, k)` with k = 0 crashes cairo ("invalid matrix"): use `max(pop(...), 1e-3)` before scaling.
- Fonts: Inter (Black/ExtraBold) for Cyrillic/Latin, "Noto Sans CJK SC" for Chinese, "DejaVu Serif"/"DejaVu Sans Mono".
  No emoji glyphs — draw icons (notes, hearts) with shapes.
- Short hex colours (#e88) are not supported — always 6 digits.
- Chips placed in the top band can collide with name tags of big characters — check stills.
- Text inside a phone/notice must be short; long sentences go to captions, not on-screen.
- Don't `pkill -f render.py` from a shell whose command line contains that string (it kills itself).
- Always look at stills before the full render (`render.py PROJ N --stills id:0.5 ...` + `preview.py sheet`).
