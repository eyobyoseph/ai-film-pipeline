# Phase 2 Experiments Log

## Experiment 1: Character-Consistent Keyframe Conditioning
- **Hypothesis:** Generating a dedicated character and visual style reference sheet first, then conditioning all 9 shot prompts on that sheet, will keep Dawit and Selam recognizably the same people across every scene.
- **Change:** Locked character descriptions (clothing, hair, facial features, warm golden-hour Ethiopian university study palette) into a master reference sheet and generated `shot_01.png` through `shot_09.png` sequentially against it.
- **Result:** Confirmed consistent character identity, lighting, and visual continuity across all 9 keyframes (`outputs/images/shot_01.png`–`shot_09.png`).

## Experiment 2: Wan 2.2 Image-to-Video with SHA-256 Input Caching
- **Hypothesis:** Conditioning `Wan-AI/Wan2.2-TI2V-5B-Diffusers` (`480x832`, 25 frames at 16 fps, 18 steps, `guidance_scale=5.0`) on each keyframe with SHA-256 input hashing (`image_hash:motion_prompt`) will animate all 9 shots cleanly while preventing duplicate GPU work after session restarts.
- **Change:** Enabled `enable_sequential_cpu_offload()`, reduced frame count from 33 to 25, added explicit `gc.collect()` + `torch.cuda.empty_cache()` cleanup after each shot, and persisted hashes in `outputs/wan_cache.json` alongside call telemetry in `outputs/wan_runs.jsonl`.
- **Result:** All 9 shots (`shot_01.mp4`–`shot_09.mp4`) rendered in ~197–201s per shot on Kaggle T4 GPU, and `shot_01` was cleanly skipped via cache after an early RAM OOM restart.

## Experiment 3: ACE-Step Score Generation & Candidate Selection
- **Hypothesis:** Generating three distinct 75-second instrumental candidates with `ACE-Step/ACE-Step-v1-3.5B` (`float32`, `cpu_offload=True`, 35 steps, `guidance_scale=12.0`) using contrasting instrumentation will provide an emotional bed that supports the proverb *ድር ቢያብር አንበሳ ያስር* without masking the Amharic narration.
- **Change:** Generated three seeded candidates in `outputs/music_candidates/` and logged latencies in `outputs/music_runs.jsonl`:
  1. `candidate_1_warm_ethiopian_folk.wav` (seed `101` — krar harp & washint flute)
  2. `candidate_2_cinematic_piano_strings.wav` (seed `202` — solo piano & cello swell)
  3. `candidate_3_minimal_ambient_marimba.wav` (seed `303` — warm marimba, gentle acoustic guitar fingerpicking, soft pad)
- **Result:** Selected **`candidate_3_minimal_ambient_marimba.wav`** because its interlocking marimba and acoustic guitar rhythm conveys a warm sense of **togetherness** and steady collaboration that matches the film's message.
