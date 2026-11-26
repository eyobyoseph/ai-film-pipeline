# Project Report: ድር ቢያብር አንበሳ ያስር (When Spider Webs Unite, They Can Tie Up a Lion)
**Author:** Eyob Getachew Yoseph
**Repository:** ai-film-pipeline (python run_pipeline.py / make film)
**Runtime & Exports:** 76.0 seconds (72.0s narrative + 4.0s end card) in 9:16 (720x1280) and 16:9 (1280x720)

## 1. Executive Summary & Creative Intent
This project implements an end-to-end, reproducible AI short film pipeline illustrating the traditional Amharic proverb «ድር ቢያብር አንበሳ ያስር» (When spider webs unite, they can tie up a lion). Set in an Addis Ababa library, the 9-shot narrative follows Dawit—a student struggling late into the evening with a stubborn software bug—and his classmate Selam, who combines her algorithmic skill with his mathematical domain insight to solve the problem together.
Rather than manual timeline editing, the entire film is compiled programmatically from a single validated JSON contract (storyboard.json). Running python run_pipeline.py (or make film) validates the schema, synthesizes Amharic TTS narration, conditions character-consistent keyframes, caches Wan 2.2 image-to-video clips by SHA-256 hash, sidechain-ducks an ACE-Step ambient marimba score (-16 LUFS), burns in English subtitles, appends a 4-second proverb end card, and exports both vertical (9:16) and widescreen (16:9) masters.

## 2. System Architecture & Cost Summary
- Contract-First Orchestration: validate_storyboard.py enforces schema/storyboard.schema.json across all 9 shots before any API or GPU call runs.
- Visual & Audio Consistency: A master reference sheet (character_ref_sheet.png) anchors Dawit and Selam across keyframes. Out of three ACE-Step musical candidates, Candidate 3 (minimal ambient marimba) was selected because its wooden percussion complements Amharic speech frequencies without masking narration.
- Observability & Budget (runs.jsonl & COSTS.md): All 84 model and pipeline calls were logged in runs.jsonl. Out-of-pocket financial spend was $0.00 USD, achieved by running Wan 2.2 (fp16) and ACE-Step (v1-3.5B) within Kaggle free weekly T4 GPU quota (~2.05 GPU hours) and executing FFmpeg mastering locally on CPU.

## 3. Iteration & User Testing
- User Test 1 (Phase 1 Audio-Only Radio Cut): Three listeners reviewed the 72-second Amharic narration before spending GPU quota. All three praised the emotional turning point in Shot 6 and the proverb reveal in Shot 8, while Listener 3 flagged Amharic gemination/stress friction (የቃላት ማጥበቅ እና ማላላት ችግር). Adjusting Amharic spelling and word spacing in storyboard.json (ቤተ-መጻሕፍት ውስጥ -> ቤተ መፅሃፍ ውስጥ and የዳዊት ትዕግሥትና -> የዳዊት ትዕግስት እና) resolved the TTS phrasing.
- User Test 2 (Phase 3 Near-Final Video Cut - outputs/final_9x16.mp4): Three viewers evaluated the near-final video. Viewer 1 praised the pacing, transitions, audio mix, and subtitles as looking professionally edited. Viewer 2 highlighted the spider-web and Selam approach shots while flagging character continuity drift. Viewer 3 noted that both characters' faces and hairstyles changed within a single-day timeline and observed that contrasting Dawit's patience with Selam's coding skills made the teamwork feel one-sided rather than merging two complementary areas of expertise. Based on this feedback, we retained the -16 LUFS audio mix and subtitles, tightened facial/hairstyle anchors and balanced Dawit's mathematical logic with Selam's algorithmic skill in storyboard.json, and documented Wan 2.2 I2V cross-shot appearance drift as a primary technical limitation.

## 4. Reflection: Suggested Practices vs. My Instinct
### Case 1: Where a Suggested Practice Beat My Instinct — Audio-Only Radio Cut & JSON Contract First
- My Instinct: I initially wanted to generate images and Wan 2.2 video clips for Shot 1 immediately so I could judge the film visually.
- What Happened: Locking storyboard.json first and testing the audio-only radio cut with three listeners exposed Amharic TTS stress issues and tight 8-second boundary pacing before I spent a single minute of Kaggle T4 GPU quota.
- Why It Beat My Instinct: Fixing text in storyboard.json took 30 seconds on CPU; re-rolling all 9 Wan 2.2 video clips on Kaggle after changing shot timing would have burned over an hour of limited weekly GPU quota.
### Case 2: Where a Suggested Practice Did Not Beat My Instinct — Decoupling Remote GPU Artifacts Behind Local SHA-256 Hashes
- The Suggested Practice: Executing every model stage sequentially in a single live local pipeline run.
- Why My Instinct Diverged: My Windows laptop runs on CPU without a high-VRAM NVIDIA GPU, while Kaggle T4 notebooks hit bfloat16 decoder incompatibilities and dependency conflicts (spacy/py3langid) that required switching to float16.
- Resolution: Decoupling heavy GPU inference into cached Kaggle artifacts (outputs/videos/*.mp4 and outputs/music_candidates/*.wav) verified by SHA-256 hashes in run_pipeline.py made local builds 100% deterministic, crash-proof, and fast (~25 seconds for both 9:16 and 16:9 masters).

## 5. Ethics & AI Disclosure
All keyframes, image-to-video motion, background marimba music, and synthesized Amharic narration were generated using AI models under human scriptwriting, cultural direction, and iterative user testing, with explicit AI labels on public release.
