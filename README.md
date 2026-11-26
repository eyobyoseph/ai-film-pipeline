# ድር ቢያብር አንበሳ ያስር (When Spider Webs Unite, They Can Tie Up a Lion)

End-to-end AI short film pipeline driven by `storyboard.json`.
Outputs `outputs/final_9x16.mp4` (720x1280) and `outputs/final_16x9.mp4` (1280x720).

## Quickstart
1. Install dependencies:
       pip install jsonschema pillow imageio-ffmpeg requests python-dotenv
2. Run the full pipeline (Windows / cross-platform):
       python run_pipeline.py
   Or on Linux/macOS:
       make film

## Pipeline Stages
- `validate_storyboard.py`: Enforces `schema/storyboard.schema.json`.
- `generate_radio_cut.py`: Synthesizes Amharic TTS narration (`outputs/narration_full.wav`).
- `generate_images.py`: Generates character reference sheet and conditioned keyframes.
- `assemble_final.py`: Sidechain-ducks marimba score, burns English subtitles, normalizes to -16 LUFS, adds 4s end card, exports 9:16 & 16:9.
- `runs.jsonl`: Unified log of all 84 model/API calls.
