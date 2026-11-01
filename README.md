# Cartoon Studio

Engine for the **cartoon-studio** Claude skill: turns one idea into a finished vertical (9:16) cartoon for
TikTok / Reels / Shorts — narration, word-by-word karaoke captions, music and sound effects.

- `kit/` — renderer (pycairo), characters, 18 styles, captions, voice alignment, audio mix, previews, free Mac narration
- `library/` — saved character casts
- `references/` — instructions the skill reads (interview, story, styles, scene API, voice)
- `SKILL.md` — source copy of the skill instructions

Claude fetches this repository automatically when the skill runs:
`git clone --depth 1 https://github.com/Wystmpll/cartoon-studio ~/cs`
