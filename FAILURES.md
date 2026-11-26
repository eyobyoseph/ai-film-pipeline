# Phase 2 Failures & Mitigations Log

## Failure 1: Missing `ftfy` Text Normalization Dependency in Wan 2.2
- **Symptom:** `NameError: name 'ftfy' is not defined` during `WanImageToVideoPipeline` prompt preprocessing across all 9 shots (`wan_runs.jsonl`).
- **Root Cause:** `diffusers` imports `ftfy` lazily inside the Wan 2.2 pipeline without installing it by default.
- **Mitigation:** Installed `ftfy` and `regex` (`pip install ftfy regex`) and patched `diffusers.pipelines.wan.pipeline_wan_i2v.ftfy` in-memory to avoid reloading the 34.2 GB model weights.

## Failure 2: Kaggle System RAM Out-of-Memory (OOM) Spike During VAE Decode
- **Symptom:** Notebook kernel crashed and restarted immediately after finishing `shot_01.mp4` and denoising `shot_02` (`Your notebook tried to allocate more memory than is available`).
- **Root Cause:** `enable_model_cpu_offload()` retained large tensors in host RAM during 33-frame 3D VAE video decoding, exceeding Kaggle's 30 GB system RAM ceiling.
- **Mitigation:** Switched to `pipe.enable_sequential_cpu_offload()`, reduced `num_frames` from `33` to `25`, added `del output; gc.collect(); torch.cuda.empty_cache()` after each clip, and resumed from `shot_02` via `wan_cache.json`.

## Failure 3: Python 3.13 Dependency Lock & `py3langid` Incompatibility in ACE-Step
- **Symptom:** `ERROR: No matching distribution found for spacy==3.8.4` on Kaggle's Python 3.13 environment, followed by `AttributeError: type object 'LanguageIdentifier' has no attribute 'from_pickled_model'` in `LangSegment`.
- **Root Cause:** ACE-Step pinned older Python <=3.12 package versions and invoked a deprecated `py3langid` classmethod even in pure instrumental mode (`lyrics="[inst]"`).
- **Mitigation:** Installed ACE-Step with `--no-deps` alongside Python 3.13-compatible packages (`spacy>=3.8.7`, `py3langid`) and monkey-patched `LanguageIdentifier.from_pickled_model` and `LangSegment.getTexts` to return `"en"`.

## Failure 4: NVIDIA T4 `bfloat16` Execution Engine Error in ACE-Step Decoder
- **Symptom:** `RuntimeError: GET was unable to find an engine to execute this computation` after 35/35 diffusion steps when decoding audio (`music_runs.jsonl`).
- **Root Cause:** NVIDIA T4 (Turing architecture, compute capability 7.5) lacks native hardware `bfloat16` kernels needed by ACE-Step's `MusicDCAE` decoder.
- **Mitigation:** Initialized `ACEStepPipeline(dtype="float32", cpu_offload=True)`, allowing all three 75-second `.wav` candidates to decode and save cleanly.

## Failure 5: Missing System `ffprobe` / `ffmpeg` on Local Windows PATH
- **Symptom:** `FileNotFoundError: [WinError 2] The system cannot find the file specified` when calling `ffprobe` via `subprocess.run()` on Windows.
- **Root Cause:** Standalone FFmpeg binaries were not registered in the Windows system `PATH`.
- **Mitigation:** Installed `imageio-ffmpeg` in Miniconda and resolved the bundled binary path via `imageio_ffmpeg.get_ffmpeg_exe()` and `imageio_ffmpeg.count_frames_and_secs()`.
