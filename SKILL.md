---
name: cartoon-studio
description: Make finished cartoon films for TikTok/Reels/Shorts — vertical 9:16 animated story videos with narration, word-by-word karaoke captions, music and sound effects — from one idea, through a guided interview, 18 drawable styles, a reusable character library and free ElevenLabs-quality narration (Qwen3-TTS on a Mac). Use this whenever someone wants a мультфильм, мультик, анимация, анимированный ролик, рилс/тикток с персонажами, a story or series about their friends, school or dorm, "сделай видео как вот это" with a reference clip, a survival/horror/comedy/romance/detective cartoon, a multi-part series with cliffhangers, or wants a script voiced for free — even if they don't say "cartoon".
---

# Cartoon Studio

Turns one idea into a finished vertical cartoon: interview → story → cast and style → narration → animation →
mixed MP4, with three checkpoints where the user approves. Everything is drawn with code (pycairo vector graphics),
so any look the kit can draw is available; photorealism and AI-generated images are not.

The proven result to aim for: 2-minute parts in the style of the "survival.loop" TikTok series — big karaoke captions,
sticky notes, timers, flat characters with expressive faces, a cut every 3-10 s, a cliffhanger at the end of each part.

## Files in this skill
- `kit/` — the engine. `render.py` (scenes → video), `audio.py` (music + SFX + mix → FINAL mp4), `align.py` (voice →
  word timings), `tts_dev.py` (free robotic draft voice), `preview.py` (character sheet, style grid, storyboard frames),
  `world.py` (sets, props, FX, UI), `chars.py` (characters), `styles.py` (18 styles), `captions.py`, `engine.py`,
  `mac_voice/` (free local narration for the user's Mac), `check_env.sh`.
- `references/interview.md` — the question bank (read before interviewing).
- `references/story.md` — pacing, structure, text rules, real-people rules, checkpoint 1 package.
- `references/characters.md` — character spec, library, making a cast distinct.
- `references/styles.md` — the 18 styles and how to compose scenes in each.
- `references/scene-api.md` — how to write scene code + pitfalls (read before writing scenes).
- `references/voice.md` — narration options and exact steps (read before the voice step).
- `library/*.json` — saved casts (e.g. `npu_friends`).

If the folder holds only SKILL.md (no `kit/`), the kit is missing — see "Getting the kit" at the end.

## Setup (every session)
```bash
SK=<this skill's directory>          # where this SKILL.md lives
mkdir -p ~/cs && cp -r $SK/kit $SK/library ~/cs/
bash ~/cs/kit/check_env.sh            # pycairo, numpy, pillow, ffmpeg, fonts
```
Work on the copy (`~/cs/kit`), never inside the skill folder. One project = one folder (e.g. `~/films/zombie`):
`project.json`, `script.py`, `scenes_p<N>.py`, optional `characters.json`; the kit writes `timing/`, `voice/`, `out/`.
Use a task list: interview, checkpoint 1, cast+style, checkpoint 2, voice, scenes per part, render, checkpoint 3, lessons.

`project.json`:
```json
{"title": "Зомби в НПУ", "style": "chibi", "lang": "ru", "libraries": ["npu_friends"], "music": "horror",
 "cast": ["Нурали", "Талейран"], "handle": "@npu.zombie",
 "parts": {"1": {"end": ["часть 2", "УМРИ, УМРИ"]}, "2": {"end": ["конец", "ВТОРОЙ ПУТЬ"]}}}
```
`script.py`: `PARTS = {1: [("scene_id", ["line", "line"]), ..., ("end", [])]}`, plus `TTS_FIX` (stress spellings
like `{"Нурали": "Нурал+и"}` for the draft synth), `KEY_RED` / `KEY_YEL` (caption highlight words).

## Step 0 — a reference video (if the user sends one)
Study it before asking anything, and skip the questions it answers. Duration and frames with ffprobe/ffmpeg; contact
sheets `fps=1/3,scale=288:-1,tile=4x2`; read the narration from a caption strip
(`fps=2,crop=W:110:0:Y,scale=…,tile=4x20` with Y on the caption band) — speech recognition models can't be
downloaded in the workspace, so captions are the transcript. Note: palette, caption look, stickers/timers, cut rhythm,
narrator voice (pitch via autocorrelation ≈ 100-130 Hz = deep male), structure (hook, rules of three, cliffhanger).
Summarise the style in 3-5 lines to the user.

## Step 1 — interview
Read `references/interview.md`. Blocks A-H: format, genre/tone, place, characters (the biggest), style, narration,
sound, process. Up to ~50 questions is fine, but never re-ask what is known (conversation, library, reference).
Choices via AskUserQuestion (≤4 per call); free-text blocks as numbered lists. Offer a default for everything —
"сам выбери" is a valid answer: decide and say what you chose. Echo each block back in 1-2 lines.
**Spoiler-free mode**: the user wants to be surprised → ask only about inputs, never show the plot; checkpoint 1 is
a logline. If they will voice it themselves, give the text as files and say "вставь целиком, не читая".

## Step 2 — story → checkpoint 1
Read `references/story.md`. Pace ≈ 2.3 words/s: 2 min ≈ 250-270 Russian words (~1500 chars); 13-20 scenes per part;
a 4 s end card per part. Every named character gets a beat only they could do. Plant clues early, pay them off later.
Write `script.py`, count words per part (`re.findall(r"\w+")`), then show the package: title, parts + titles, 3-5
line synopsis each (or logline), cast with roles, style, voice, music. Ask «Утверждаем или что поменять?».

## Step 3 — cast and style → checkpoint 2
Read `references/characters.md` and `references/styles.md`. Reuse library characters; new ones go to
`characters.json`. Make the cast distinct (height, width, hair shape, one signature colour, one accessory each).
Then: `python ~/cs/kit/tts_dev.py PROJ 1` (draft voice → timings, so scenes can be timed now), write 3-4 key scenes,
and render `preview.py chars PROJ` + `preview.py frames PROJ 1 id:0.6 …` (+ `preview.py styles …` if the style is
undecided). Look at every image yourself first (overlaps, cropped heads, unreadable text), fix, then send the
character sheet and frames with SendUserFile. Ask for approval or changes.

## Step 4 — narration
Read `references/voice.md` and pick with the user:
- **A. Qwen3-TTS on their Mac** (free, close to ElevenLabs, voice design + cloning, Russian and English) — default for
  Mac users. One-time setup in Terminal, then one command per part; Claude reads the result from the connected folder.
- **B. ElevenLabs** (their account) — give one .txt per part, they send mp3s back.
- **C. edge-tts** Microsoft voices (free, decent) — from their computer.
- **D. RHVoice draft** (`tts_dev.py`) — robotic; drafts and last resort.
Then `python ~/cs/kit/align.py PROJ N <audio>` (one long file, pause-based) or `--lines DIR` (one wav per line,
exact). Check the printed segments: each line of text should sit on its own segment; a cost per segment under ~1.5
means a clean match. If a voice file can't be matched (missing sentence, extra words), tell the user which line.
Map ElevenLabs files to parts by the timestamp in their names. Keep at most 3-4 permanent voices per user.

## Step 5 — scenes
Read `references/scene-api.md`. One function per scene id in `scenes_p<N>.py`, anchored to words (`S.w("слово")`) and
lines (`S.L(i)`) so it survives a new voice with different timing. Compose in the language of the chosen style. Every
scene needs motion (walk, camera push, pop-ins, FX) and 1-3 SFX on real events (`S.sfx("door", S.w("дверь"))`).
Review stills before rendering: `render.py PROJ N --stills id:0.3 id:0.8 …` then `preview.py sheet` — check every
scene once at two moments. Typical fixes: chips colliding with name tags, faces under captions (keep faces above
y≈850), a tiny character in a big empty frame, text too long for a phone or notice.

## Step 6 — render, mix, verify → checkpoint 3
```bash
python ~/cs/kit/render.py PROJ N          # run in background for long parts; ~1-2 min per minute of video
python ~/cs/kit/audio.py PROJ N           # music (project mood) + SFX + voice normalised to -15 LUFS → out/FINAL_pN.mp4
```
Verify before sending: duration (≈ narration + end card), `volumedetect` mean ≈ -16 dB, a 1/5 fps contact sheet of
the final file (captions present and in sync with scene content, nothing cropped). Name files so they sort
(`<title>_chast1.mp4`) and send all parts with SendUserFile. Say honestly what you checked (frames, loudness) and
what you couldn't (you can't listen to the audio).

## Step 7 — learning loop (after every film)
Ask three short questions: what to keep, what to change, what was missing. Then:
1. Add new characters / changed looks to the library JSON (looks + neutral traits only).
2. Add 1-5 concrete lessons to "Lessons" below (what to do differently and why).
3. Propose the updated skill to the user (propose_skills with the full new SKILL.md); library or kit changes go into
   the kit source (see "Getting the kit").
Keep lessons general enough to help the next, different film.

## Lessons (from real films)
- Users love seeing their real friends' quirks become plot beats (a rumour paid off as a climax, a habit that saves
  everyone). Ask for quirks and inside jokes; they make the film.
- A known structure works: hook to the viewer → rules of three → «На бумаге — всё идеально. Была лишь одна
  проблема.» → twist → cliffhanger title for the next part.
- Don't reuse a plot the user has already read — in spoiler-free mode write a new one.
- ElevenLabs voices differ in loudness by 10 dB; always normalise the voice in the mix (audio.py does).
- Russian stress in names: for the draft synth use `+` in TTS_FIX; for ElevenLabs/Qwen respell or regenerate the line.
  Letters after «блок» must be written out for TTS («блок Эс»).
- A user who will narrate in ElevenLabs needs ≈ 1500 chars per 2-minute part; the free tier is 10 000 chars/month —
  warn before writing 4+ parts.
- Prior films: the NPU dorm survival series and the zombie apocalypse (chibi style, 4 parts) — the user liked both;
  asked for "even better": richer animation, more expressive faces, distinct characters.

## Safety and taste
Films are often about real people, some may be minors: affectionate humour only; nothing sexual; no humiliation; no
exposing private facts (health, orientation, family tragedies) unless the user says the person is fine with it — and
then gently. No real public figures or copyrighted characters/costumes (draw an original look even if a friend's
nickname is a superhero). Voice cloning only from a sample of a person who agreed (the user, or a friend who recorded
it themselves) — never celebrities or TikTok narrators. Music: synthesised score only; tell users to add trending
songs inside TikTok.

## Getting the kit
The kit is ~3000 lines of Python plus the library and references; it must sit next to this file. If it's missing,
look for it in the user's files (a `cartoon-studio-kit.zip` they may attach) and unpack it beside SKILL.md's copy in
`~/cs/`. Without the kit, tell the user what's missing rather than rebuilding the engine from scratch.
