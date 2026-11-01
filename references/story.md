# Writing the film

## Length and pace
- Narration pace ≈ 2.2-2.4 words/second. 2 minutes ≈ 250-270 Russian words (~1500 characters). 60 s ≈ 130 words.
- Keep a 4 s end card per part ("часть 2 / TITLE"); it is the empty scene `("end", [])`.
- A scene = one visual idea = 1-4 lines = 3-10 s. ~13-20 scenes per 2-minute part. Never one picture for 15 s.

## Structure that works (proven on the survival-style videos)
1. Hook in the first line, addressed to the viewer: «Если X застал вас в Y — не делайте Z. Даже если…».
2. Setup: place, time stamp, the rule of the world, the cast in one quick line each (trait shown, not told).
3. Plan / rules of three: «Первое — … Второе — … Третье — …».
4. «На бумаге — всё идеально. Была лишь одна проблема.» → complication.
5. Escalation with each character getting a beat that shows their trait.
6. Twist that re-reads earlier clues (plant clues early, pay them off later: rumours, objects, habits).
7. Cliffhanger at the end of every part except the last; a short punchy title for the next part.
Variety: not every film is survival. Comedy = setup → escalation → absurd payoff; romance = longing → obstacle →
small gesture; explainer = question → 3 facts → surprising answer.

## Characters on screen
- Everyone named in the brief gets at least one beat that only they could do (their trait solves or causes something).
- Distinct silhouettes: height, width (bw), hair shape, one signature colour per person, one accessory. Check the
  character sheet: if two people read the same at thumbnail size, change hair or colour.
- Show emotion with mood (happy, scared, angry, sad, smug, focus), mouth (talk, shout, laugh, smirk, o), shake, lean, arms.

## Text rules
- Short sentences. One fact per sentence. Numbers as words in the script (for TTS), digits on screen.
- Write names exactly as the user does; stress marks go in TTS_FIX (`"Нурали": "Нурал+и"`), not in the text.
- Write «блок С» etc. as you want it shown; tts_dev fixes letters after «блок». For ElevenLabs/Qwen write it phonetically
  in the job/text you hand over («блок Эс»).
- KEY_RED (danger words) and KEY_YEL (names auto-added, numbers auto) drive caption colours.

## Real people
These films are often about the user's real friends. Keep them affectionate: no sexual content (some may be minors),
no humiliation, no exposing private facts (health, orientation, family tragedies) unless the user says the person is
fine with it — and even then keep it light and respectful. Do not depict real public figures or copyrighted characters
(no Spider-Man costume even if a friend's nickname is "Спайдермен").

## Checkpoint 1 package (show the user)
Title, parts with their titles, per part a 3-5 line synopsis (or logline only in spoiler-free mode), cast with roles,
style, voice, music. Ask: «Утверждаем или что поменять?»
