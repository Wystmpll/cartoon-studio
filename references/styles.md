# Style catalog (18)

Set `"style": "<key>"` in project.json. `styles.apply()` changes character knobs, recolours every background
(all background colours go through `pal()`), post-processes frames and restyles captions. The style only does part
of the job: **compose scenes in the language of the style** (table below). Show users the grid
(`python preview.py styles PROJ 1 <scene> 0.8`) when they can't decide.

| # | key | Название | Best for | Compose scenes like this |
|---|-----|----------|----------|--------------------------|
| 1 | survival | Ночной флэт | survival «Если X застал вас…», thrillers | Night exteriors, building cross-sections (`building(cut=True)`), stickers `sticky`, timers `clockchip`, counters, rules «1. 2. 3.» |
| 2 | chibi | Чиби-флэт | comedy, school/dorm life | Big expressive faces, close-ups (`closeup2`), bubbles, hearts, bright day sets |
| 3 | anime | Аниме | drama, action, romance | Dramatic close-ups, `speed_lines` on reveals, sunsets, wind/dust, low angles (cam), cel shading is automatic |
| 4 | comic | Комикс | action, parody | Split screens with `panel()` as comic panels (2-4 per scene), `burst("БАМ!")`, bold poses; captions become yellow boxes |
| 5 | papercut | Бумажная аппликация | fairy tales, kids | Few large flat props, layered depth, slow parallax; stepped animation is automatic (on 2s) |
| 6 | pixel | Пиксель-арт | gamer stories | Side-view like a platformer, simple big shapes (detail is lost), HUD-like chips (HP, score, timers) |
| 7 | doodle | Каракули в тетрадке | memes, explanations | `paper_bg("notebook")` or plain light rooms, arrows, handwritten-looking labels, stick-simple props |
| 8 | noir | Нуар | detective, thriller | Night, rain overlay (automatic), hard light cones (`light_cone`), silhouettes (`sil=True`), red as the only colour (blood, lipstick, sign) |
| 9 | isometric | Изометрия | heists, "who was where", plans | `iso_room()` + `iso_box()` furniture, small characters (H≈150) placed with the returned P2(u,v) |
| 10 | retro30 | Ретро 1930-х | absurd comedy, parody | Bouncy walks, pie eyes (automatic), iris-in/out (darken with radial), intertitle captions |
| 11 | soviet | Тёплая аппликация | nostalgia, kind stories | Daylight, calm compositions, warm props, slow camera |
| 12 | neon | Неон-киберпанк | sci-fi, hackers, night city | Dark `street()`, glowing signs (`glow`), phones/screens, glitch is automatic |
| 13 | watercolor | Акварель | romance, sadness, memories | Day/dusk, soft light, few elements, slow pacing, hearts/petals |
| 14 | clay | Пластилин | absurd comedy, kids | Chunky props, close-ups, squash-and-stretch with `pop()` |
| 15 | explainer | Объяснялка-схема | facts, how-to, rankings | Light background, `arrow()`, counters, charts drawn with rectangles, icons, numbered stickers |
| 16 | horror | Хоррор-скетч | horror, creepypasta | Darkness, single light, `flash_red`, `handheld()` shake, slow reveals, zombies/silhouettes |
| 17 | lowpoly | Псевдо-3D | game-like, tech | Big simple shapes, strong light from one side, faceting is automatic |
| 18 | truecrime | Доска улик | investigations, "who did it" | Every scene as `polaroid()` photos on `paper_bg("cork")` + `red_string`, typewriter captions |

Mixing: pick the base style and borrow one compositional element from another (e.g. noir + comic panels).
Light styles (doodle, explainer, watercolor, papercut, soviet) have dark captions — keep important overlays dark
or saturated, not white.

## Knobs (engine.STYLE) — for custom styles
head_scale, eye ("round" | "anime" | "pie" | "dot"), outline (px at 260px height), outline_col, drop_shadow, cel, clay,
neon (glow colour), wobble (px boil), step (animate on 2s/3s). New style = one `style(...)` call in styles.py:
background `remap(light=(a,b) | lmul, sat, hue_to, hue_k)`, `post=(("grain",12),("bloom",0.4),...)`, caption dict.
Post ops: grain, paper, gouache, lowpoly, gray_red, gray_sepia, desat, posterize, pixel, halftone, bloom, blur, chroma,
flicker, jitter, glitch (+ vignette).
