# System Architecture

## 1. Contract-Driven Pipeline
`storyboard.json` (9 shots, 72.0s + 4.0s end card = 76.0s) is the single source of truth.

## 2. Stages & Data Flow
1. **Schema Validation (`validate_storyboard.py`):** Fails fast on invalid shot structure or duration mismatch.
2. **Amharic Narration (`generate_radio_cut.py`):** Generates per-shot Amharic TTS and full voiceover track.
3. **Visual Consistency & Video (`generate_images.py` + Kaggle Wan 2.2):** Anchors Dawit and Selam via a reference sheet before generating shot keyframes and I2V clips.
4. **Musical Score (Kaggle ACE-Step):** Generated 3 candidates; selected `candidate_3_minimal_ambient_marimba.wav`.
5. **Final Mastering (`assemble_final.py`):** Dynamic FFmpeg `sidechaincompress` ducking, burned-in SRT subtitles, `-16 LUFS` EBU R128 loudness normalization, 4s proverb end card, and dual `9:16` + `16:9` exports.
6. **SHA-256 Caching (`outputs/.pipeline_cache.json`):** Re-running `python run_pipeline.py` skips unchanged shots and regenerates only modified shots.
7. **Observability (`runs.jsonl`):** Logs every call (84 total records).
