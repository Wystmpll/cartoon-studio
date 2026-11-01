# Characters

## Spec (JSON, one entry per name)
```json
"Нурали": {"h": 185, "skin": "#e9b98f", "hair": "curly", "hc": "#2a1a12", "top": "hoodie", "tc": "#e8833a",
           "t2": "#c96a26", "pants": "#2b3550", "shoes": "#f2f2f2", "acc": [], "bw": 1.06,
           "about": "спокойный гений, шутит не в тему", "tts": "Нурал+и"}
```
- h: height in cm (relative heights matter: the tallest really is tallest). bw: body width 0.85 (slim girl) … 1.3 (big).
- hair: curly slick quiff curtain messy short wavy bangs buzz side cap volume bun long fade.
- top: hoodie hoodup coat jacket shirt tee track blazer jersey crop cardi pj (t2 = secondary colour: lapels, stripes, numbers).
- acc: scarf thread chain mono phones glasses beard watch grin lashes hoops shades band sleepy stink bandage sleeve tie.
- girl: true (slimmer). eye: iris colour for anime style. Optional "about", "tts" (stress spelling), "mood" (default face).

## Library
`library/*.json` holds reusable casts (e.g. npu_friends.json — the user's NPU friend group; npu_extras.json).
In project.json: `"libraries": ["npu_friends"]`; project-only characters go to PROJ/characters.json (same format,
overrides library entries with the same name). After every film, add new characters and changed looks to the library
(see the learning loop in SKILL.md). Keep library entries to looks + neutral traits; no private facts about real people.

## Making the cast distinct (check on the character sheet)
1. Silhouette: height + bw + hair shape differ between people standing next to each other.
2. One signature colour per main character (tc), no two mains with the same hue.
3. One accessory or detail each (headphones, chain, headband with number, beard, glasses, hood).
4. Expression habit: default mood (smug for the cool one, focus for the leader, happy for the clown).
`python kit/preview.py chars PROJ` → out/charsheet.png. Show it at checkpoint 2.
