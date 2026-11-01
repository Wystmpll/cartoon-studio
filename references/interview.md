# Interview: the question bank

Goal: after the interview you can write the whole film without guessing. Ask in the user's language
(Russian examples below; translate for English speakers). Up to ~50 questions is fine for this user group,
but never ask what the user already told you, what the character library already holds, or what a reference
video already shows.

## How to ask
- Use AskUserQuestion for choices (max 4 questions per call, 2-4 options each, "Other" is automatic). Put free-text
  questions (names, looks, relationships) in a normal message as a numbered list, so people can answer "1) ... 2) ...".
- Go block by block (A → H). After each block, briefly echo what you understood in one or two lines, so mistakes surface early.
- Offer a sensible default for everything ("если не знаешь — выберу сам"). "Сам выбери" is a valid answer: decide and say what you chose.
- If the user sends a reference video: analyse it first (contact sheets + caption strip, see SKILL.md) and skip the
  questions it answers (style, pacing, narrator voice type, format).
- Spoiler-free mode: if the user wants to be surprised, ask only about inputs (characters, setting, genre, length, tone,
  limits) and never show the plot; checkpoint 1 becomes "logline only" (one sentence, no twists).

## A. Format (4-6 questions)
1. Где будет ролик? TikTok/Reels/Shorts (9:16) — по умолчанию.
2. Сколько частей и какой длины каждая? (1 ролик 30-60 с / серия частей по ~2 мин). Approx: 2 минуты ≈ 250-270 слов текста.
3. Язык озвучки и субтитров: русский / английский.
4. Нужен ли режим без спойлеров (сюжет держу в секрете)?
5. Подпись-никнейм в углу (например @npu.zombie) или без неё?

## B. Genre, tone, idea (6-8)
6. Жанр: выживание «Если X застал вас…», хоррор, комедия/мем, романтика, детектив, экшен, пародия, объяснялка, поздравление, реальная история.
7. Тон: серьёзный и напряжённый / ироничный / абсурдный / тёплый / мрачный.
8. Есть ли готовая идея или событие, от которого оттолкнуться? (одно-два предложения)
9. Что должно случиться обязательно (сцены-«хотелки»)? Что нельзя показывать?
10. Насколько неожиданным должен быть сюжет: «понятный и чёткий» ↔ «много поворотов».
11. Концовка: закрытая / открытая / клиффхэнгер; счастливая / грустная / «злодей победил».
12. Допустимая жёсткость: насилие (без крови / мультяшное / мрачно), страшные моменты, грубые шутки.
13. Мораль или главное чувство, которое должно остаться у зрителя?

## C. Place and world (4-6)
14. Где происходит действие? (общага, кампус, школа, город, лес, космос…) Реальное место — пришлите фото/карту или
    назовите здания; я нарисую упрощённо.
15. Как устроено место: этажи, комнаты, выходы, кто где живёт — всё, что может стать частью сюжета.
16. Время: ночь/день, сезон, погода.
17. Правила мира (зомби слепые? карантин? магия?) — или придумать мне.
18. Второстепенные места, которые должны появиться.

## D. Characters (the biggest block; per character)
First: «Кто главные герои? Перечисли имена.» Check the library (`library/*.json`) — for known characters ask only
"оставить как в библиотеке или что-то поменять?". For every new character ask (in one message, per name):
19. Рост (или «самый высокий/низкий»), телосложение.
20. Причёска и цвет волос; лицо (борода, очки, веснушки), цвет кожи.
21. Одежда / любимый стиль, фирменная вещь (цепь, наушники, кепка, джерси с номером).
22. Характер в 2-3 словах + как говорит (много/мало, шутит, тихо, на пафосе).
23. Как ведёт себя в панике (паникует, злится, застывает, хладнокровен) — gives you scene beats.
24. Отношения: кто с кем дружит, соседи, конфликты, тайные симпатии (только то, что человек готов показать).
25. Роль в сюжете: главный герой / злодей / тёмная лошадка / комик / «выбери сам».
26. Ударения в именах и прозвища (для озвучки): «НуралИ», «ТаИр».
27. Второстепенные и массовка: имена + 1 черта; кто из них «негативный».
Also ask once: 28. Можно ли упоминать черты, которые могут задеть реальных людей (ориентация, внешность, слухи)? Если
ролик пойдёт в открытый доступ — согласны ли сами ребята? (Default: keep it light, never sexual, never humiliating.)

## E. Style (3-5)
29. Стиль — покажи каталог (references/styles.md, 18 стилей) и/или сетку превью (preview.py styles). Можно смешать
    (например «комикс + нуар»): pick the closer base style and borrow one element.
30. Палитра/настроение: тёмная ночь, яркий день, тёплая, холодная, неон.
31. Насколько «живо»: спокойная подача с крупными стикерами ↔ много движения, камера, эффекты.
32. Субтитры: караоке по словам (по умолчанию), обычные, без субтитров.
33. Референсы: пришлите видео/картинки, на которые похоже.

## F. Narration (4-6)
34. Кто озвучивает: (a) я сам локально бесплатно на Mac (Qwen3-TTS), (b) ты в ElevenLabs по моим файлам,
    (c) черновой синтезатор (быстро, роботизированно), (d) бесплатные голоса Microsoft (edge-tts).
35. Голос: глубокий мужской рассказчик / молодой энергичный / женский / английский трейлерный (или свой пресет).
36. Темп: медленно и драматично / средне / быстро.
37. Эмоции: где шёпот, где крик (отметить в сценарии).
38. Один рассказчик или голоса персонажей (диалоги)?

## G. Sound (2-3)
39. Музыкальный фон: напряжённый, хоррор, грустный, комедийный, героический, загадочный, романтичный, спокойный, без музыки.
40. Звуковые эффекты: да (шаги, удары, двери, крики, вертолёт…) / минимум / нет.
41. Если нужна конкретная песня — её лучше добавить в самом TikTok (авторские права).

## H. Process (2-3)
42. Контрольные точки: (1) сюжет, (2) лист персонажей + 3-4 кадра стиля, (3) готовое видео. Оставить все или пропустить?
43. Что для тебя «идеально»? Что в прошлых роликах понравилось/бесило? (feeds the learning loop)
44. Дедлайн / сколько частей сделать сейчас.

## Learning from how the user explains
- Note the user's own words for things (e.g. "шторы" = curtain haircut, "випка" = flashy rich kid) and reuse them.
- When an answer is vague ("сделай красиво"), offer 2-3 concrete options with a one-line picture of each.
- After the film, ask 3 short questions: what to keep, what to change, what was missing. Turn the answers into
  "Lessons" in SKILL.md (see the Learning loop section there) so the next film starts smarter.
