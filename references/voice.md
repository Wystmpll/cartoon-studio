# Narration without subscriptions

How paid services like ElevenLabs work: a large neural text-to-speech model trained on thousands of hours of speech
runs on GPUs on their servers; "voice cloning" conditions the same model on a short sample. Open models of that kind
now run on a laptop. Ranking for Russian + English, best first:

| Option | Quality / emotion | Cost | Where it runs | When to use |
|---|---|---|---|---|
| A. Qwen3-TTS (Apache-2.0) via `qwen-tts-cli[mlx]` | Close to ElevenLabs; voice design from a text description, cloning from ~3 s, style instructions | free | user's Mac, Apple Silicon (M1+), natively in Terminal (MLX) | default for final voice |
| B. ElevenLabs (user's account) | Best, most emotional | free 10k chars/month, then paid | their website | user prefers it / has credits |
| C. edge-tts (Microsoft neural voices) | Good, less emotional (ru: Dmitry, Svetlana) | free, needs internet | Mac Terminal or anywhere with access | quick decent voice |
| D. RHVoice (`kit/tts_dev.py`) | Robotic | free, offline | cloud workspace | timing drafts, last resort |

The cloud workspace cannot download models (Hugging Face is blocked there) and cannot use the Mac GPU. The remote
device shell is a Linux VM without Apple GPU — so Qwen3-TTS must run in the Mac's own Terminal. Plan for it.

## A. Qwen3-TTS on the user's Mac
One-time setup (≈20-40 min, VPN on in mainland China, ~5-10 GB free disk, 16 GB RAM recommended):
1. Ask the user to create a folder `~/CartoonVoice` and connect it to this chat (Claude desktop app → "Add folder"),
   or request access with `device_request_folder_access`.
2. Copy `kit/mac_voice/voice.py` and `setup.sh` into it (`device_commit_files`, or device_bash `cat > file`).
3. User opens Terminal and runs: `cd ~/CartoonVoice && bash setup.sh` (installs Homebrew if missing, Python 3.11,
   ffmpeg, `qwen-tts-cli[mlx]`, `edge-tts`, then designs 4 starter voices: narrator_deep, narrator_young,
   narrator_female, narrator_en). Ask them to send a screenshot or the last lines if anything fails.
4. Audition: send the 4 `presets/*.wav` (stage them, then SendUserFile) — user picks favourites; new presets:
   `python voice.py design NAME "описание голоса" --lang ru` (max 3-4 permanent voices).
Per film:
1. Write `~/CartoonVoice/jobs/p<N>.json`: `{"voice": "narrator_deep", "lang": "ru", "engine": "qwen-clone",
   "lines": [{"text": "...", "instruct": "tense whisper"}, ...]}` — one entry per script line in order, text written
   phonetically where needed («блок Эс»), stress via spelling if a word comes out wrong.
   engine: qwen-clone = same timbre every line (default); qwen-design = description + per-line emotion (more
   expressive, timbre can drift — test on 5 lines first); edge = Microsoft voices.
2. User runs in Terminal: `cd ~/CartoonVoice && source .venv/bin/activate && python voice.py speak jobs/p1.json`
   (re-running skips finished lines; add `"redo_lines": [3, 7]` to regenerate specific lines).
3. When `jobs/p1/DONE` exists: stage `jobs/p1/l*.wav` into the workspace and run
   `python kit/align.py PROJ 1 --lines <staged dir>` → exact timings, voice/p1.wav.
If computer-use tools are available and the user agrees, Claude can open Terminal and run step 2 itself.
Licence: Qwen3-TTS is Apache-2.0 (commercial use OK). Never clone a real person's voice without their consent
(the user's own voice or a friend who recorded the sample himself is fine; famous narrators/celebrities are not).

## B. ElevenLabs
Give the user one .txt per part (one paragraph per scene, phonetic spellings applied). Settings that worked:
Multilingual v2, Stability ~45%, Similarity ~75%, Style 0-15%; same voice for all parts. In mainland China needs VPN.
The user uploads the mp3s; map files to parts by the timestamp in the file name; then
`python kit/align.py PROJ N path/to/file.mp3` (pause-based alignment; prints every segment with its words — check
that segments match; cost per segment < ~1.5 is good). Loudness differs between voices — the mix normalises voice
to -15 LUFS automatically.

## C. edge-tts
`edge-tts --voice ru-RU-DmitryNeural --rate=+5% --text "..." --write-media out.mp3` per line (job engine "edge").
English: en-US-GuyNeural / en-US-JennyNeural. Needs internet access to Microsoft from wherever it runs.

## D. RHVoice drafts
`python kit/tts_dev.py PROJ N [--lang en]` → timing/pN.json + voice/pN_dev.wav. Use it to build and check the
animation before the real voice exists; re-run align with the real audio later and re-render (scenes adapt to new
timings automatically because they are anchored to words/lines).
