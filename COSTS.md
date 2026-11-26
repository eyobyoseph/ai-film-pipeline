# Pipeline Compute & Cost Breakdown

- **Finished Runtime:** 76.0s (72.0s story + 4.0s end card)
- **Total Logged Calls (`runs.jsonl`):** 84
- **Total Financial Spend:** **$0.00 USD** (Free APIs + Kaggle T4 GPU quota + local CPU FFmpeg)

## Stage Breakdown
| Stage | Tool / Model | Hardware / Quota | Cost |
| :--- | :--- | :--- | :---: |
| Validation | Python `jsonschema` | Local CPU | $0.00 |
| Amharic TTS | Neural Amharic TTS (`am-ET`) | Free Cloud API | $0.00 |
| Keyframes | Conditioned Image Gen | Free API Tier | $0.00 |
| Video Motion | Wan 2.2 I2V (`fp16`) | Kaggle T4 GPU (~1.8 hrs) | $0.00 |
| Music Score | ACE-Step (`v1-3.5B`) | Kaggle T4 GPU (~0.25 hrs) | $0.00 |
| Final Edit | FFmpeg (`sidechaincompress`, `loudnorm`) | Local CPU (~25s) | $0.00 |

## Logged Calls (`runs.jsonl`)
| Engine / Identifier | Calls | Tier | Cost |
| :--- | :---: | :--- | :---: |
| `gemini-2.5-flash-preview-tts` | 27 | Free tier / Kaggle quota | $0.00 |
| `Wan-AI/Wan2.2-TI2V-5B-Diffusers` | 18 | Free tier / Kaggle quota | $0.00 |
| `@cf/black-forest-labs/flux-1-schnell` | 13 | Free tier / Kaggle quota | $0.00 |
| `gemini-3.8-flash` | 12 | Free tier / Kaggle quota | $0.00 |
| `am-ET-MekdesNeural` | 7 | Free tier / Kaggle quota | $0.00 |
| `gemini-3.5-flash-lite` | 3 | Free tier / Kaggle quota | $0.00 |
| `ACE-Step/ACE-Step-v1-3.5B` | 3 | Free tier / Kaggle quota | $0.00 |
| `gemini-2.5-flash` | 1 | Free tier / Kaggle quota | $0.00 |
