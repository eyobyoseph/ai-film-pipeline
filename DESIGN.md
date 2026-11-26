# Film Design Document

## 1. Audience & Viewing Context
- **Story:** A short narrative illustrating the Ethiopian proverb *"ድር ቢያብር አንበሳ ያስር"* ("When spider webs unite, they can tie up a lion"), showing two classmates in Addis Ababa who overcome a difficult technical problem by combining their strengths.
- **Who Will Watch This:** Ethiopian students, aspiring developers, friends, and family members in Addis Ababa and the diaspora.
- **Where They Will Watch:** Shared directly in Telegram and WhatsApp groups and viewed on mobile phone screens in **9:16 vertical format** (`720x1280`), with burnt-in English subtitles so viewers can follow easily even in noisy environments.
- **Intent (What They Should Feel & Understand):** Viewers should feel warmth, encouragement, and pride in Ethiopian wisdom—walking away understanding that struggling alone slows us down, while sharing knowledge and collaborating turns overwhelming challenges into shared victories.

## 2. Storyboard & Technical Plan
- **Target Length:** 60–75 seconds (9 shots, 6–9 seconds each) with ~140–170 words of spoken Amharic narration.
- **Visual Consistency:** Consistent character descriptions and warm Addis Ababa library/study atmosphere across all keyframes.
- **Audio Mix:** Amharic TTS voiceover at 0 dB with background music ducked to -20 dB during narration.

## 3. User Testing Log — Phase 1 (Radio Cut)
- **Listener 1 (AAU Computer Science Student, via Telegram):** Identified the proverb reveal in Shot 8 (*"ድር ቢያብር አንበሳ ያስር"*) as the strongest, most resonant line in the story, and reported that nothing felt too fast, too quiet, or confusing.
- **Listener 2 (Peer Reviewer, via Telegram):** Highlighted Selam walking over to help Dawit as the emotional turning point and the proverb reveal (*"ድር ቢያብር አንበሳ ያስር"*) paired with the closing call to share knowledge as the strongest lines; noted that the Amharic narration pacing and volume were clear and steady, though the completely black video track without visuals or captions would be confusing if animations were intended.
- **Listener 3 (Native Amharic Speaker, via Telegram):** Noted an Amharic intonation and stress issue (*የቃላት ማጥበቅ እና ማላላት ችግር* — gemination/stress placement) in parts of the synthesized TTS narration.
- **What We Changed Based on Feedback:** Adjusted Amharic spelling and word spacing in `storyboard.json` for `shot_03` (`ቤተ-መጻሕፍት ውስጥ` → `ቤተ መፅሃፍ ውስጥ`) and `shot_07` (`የዳዊት ትዕግሥትና` → `የዳዊት ትዕግስት እና`) and regenerated `narration_full.wav` to improve TTS phrasing and stress; proceeded to Phase 2/3 visual keyframe animation and burned-in subtitles to replace the audio-only black screen.

## 4. User Testing Log — Phase 3 (Near-Final Cut: `outputs/final_9x16.mp4`)
- **Viewer 1 (Audience Reviewer, via Telegram):** Praised the pacing and transitions as looking like a professional edit, and confirmed that the audio mix (Amharic narration over ducked marimba) and burned-in English subtitles were clear and well-executed.
- **Viewer 2 (Audience Reviewer, via Telegram):** Highlighted the opening spider-web shot and Selam walking over to Dawit as the standout moments, and confirmed that the English subtitles were easy to read and the Amharic narration was loud and clear, while noting visual continuity drift in the main character across shots.
- **Viewer 3 (Audience Reviewer, via Telegram):** Noted that both characters' hairstyles and facial features drifted across shots despite the story taking place in a single day, and pointed out a narrative imbalance: contrasting Dawit's patience with Selam's coding skills made it feel one-sided rather than showing two distinct areas of expertise combining to solve the problem.
- **What We Changed Based on Feedback:** Kept the validated audio mix (-16 LUFS), burned-in English subtitles, and 4-second proverb end card unchanged after unanimous positive audio/subtitle feedback; revised `storyboard.json` character identity anchors (locking Dawit's short curly hair, glasses, and olive jacket, and Selam's braided hair and burgundy cardigan) and updated `shot_07` narrative framing so Dawit's mathematical modeling/domain logic explicitly combines with Selam's algorithmic debugging; documented Wan 2.2 I2V cross-shot facial/hairstyle drift as a key architectural limitation in `DESIGN.md`, `FAILURES.md`, and `REPORT.md`.
