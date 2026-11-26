import os
import json
import glob
import subprocess
import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "outputs")
VID_DIR = os.path.join(OUT_DIR, "videos")
MUSIC_FILE = os.path.join(OUT_DIR, "music_candidates", "candidate_3_minimal_ambient_marimba.wav")
ROUGH_CUT = os.path.join(OUT_DIR, "rough_cut.mp4")

def write_docs():
    experiments_md = """# Phase 2 Experiments Log

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
"""

    failures_md = """# Phase 2 Failures & Mitigations Log

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
"""

    with open(os.path.join(BASE_DIR, "EXPERIMENTS.md"), "w", encoding="utf-8") as f:
        f.write(experiments_md)
    with open(os.path.join(BASE_DIR, "FAILURES.md"), "w", encoding="utf-8") as f:
        f.write(failures_md)
    print("[OK] Wrote EXPERIMENTS.md and FAILURES.md")

def find_narration():
    patterns = [
        os.path.join(OUT_DIR, "**", "*narration*.wav"),
        os.path.join(OUT_DIR, "**", "*narration*.mp3"),
        os.path.join(OUT_DIR, "**", "*voice*.wav"),
        os.path.join(OUT_DIR, "**", "*voice*.mp3"),
        os.path.join(OUT_DIR, "**", "radio_cut.mp4"),
        os.path.join(OUT_DIR, "**", "*.mp3"),
    ]
    for pat in patterns:
        hits = [p for p in glob.glob(pat, recursive=True) if "music_candidates" not in p]
        if hits:
            return hits[0]
    return None

def get_duration(path):
    try:
        _, secs = imageio_ffmpeg.count_frames_and_secs(path)
        return float(secs) if secs > 0 else 1.56
    except Exception:
        return 1.56

def build_rough_cut():
    temp_dir = os.path.join(OUT_DIR, "temp_norm")
    os.makedirs(temp_dir, exist_ok=True)

    sb_path = os.path.join(BASE_DIR, "storyboard.json")
    durations = {f"shot_{i:02d}": 8.0 for i in range(1, 10)}
    if os.path.exists(sb_path):
        with open(sb_path, "r", encoding="utf-8") as f:
            sb = json.load(f)
        for s in sb.get("shots", []):
            if "shot_id" in s and "duration_sec" in s:
                durations[s["shot_id"]] = float(s["duration_sec"])

    concat_list = os.path.join(temp_dir, "concat.txt")
    with open(concat_list, "w", encoding="utf-8") as cf:
        for i in range(1, 10):
            shot_id = f"shot_{i:02d}"
            raw_mp4 = os.path.join(VID_DIR, f"{shot_id}.mp4")
            if not os.path.exists(raw_mp4):
                raise FileNotFoundError(f"Missing video clip: {raw_mp4}")

            raw_dur = max(get_duration(raw_mp4), 0.5)
            target_dur = durations.get(shot_id, 8.0)
            pts_factor = target_dur / raw_dur
            norm_mp4 = os.path.join(temp_dir, f"{shot_id}_norm.mp4")

            cmd = [
                FFMPEG_EXE, "-y", "-i", raw_mp4,
                "-vf", f"setpts={pts_factor:.4f}*PTS,scale=720:1280:flags=lanczos,fps=24,format=yuv420p",
                "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                norm_mp4
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            safe_path = norm_mp4.replace("\\", "/")
            cf.write(f"file '{safe_path}'\n")
            print(f"[OK] Aligned {shot_id}.mp4 ({raw_dur:.2f}s -> {target_dur:.1f}s)")

    silent_cut = os.path.join(temp_dir, "silent_72s.mp4")
    subprocess.run([
        FFMPEG_EXE, "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c", "copy", silent_cut
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    narration_file = find_narration()
    assert os.path.exists(MUSIC_FILE), f"Missing selected music file: {MUSIC_FILE}"

    if narration_file:
        print(f"[INFO] Mixing narration ({os.path.basename(narration_file)}) + candidate_3 music...")
        cmd = [
            FFMPEG_EXE, "-y",
            "-i", silent_cut,
            "-i", narration_file,
            "-i", MUSIC_FILE,
            "-filter_complex",
            "[1:a]volume=1.0[vo];[2:a]volume=0.18,afade=t=in:st=0:d=2,afade=t=out:st=69:d=3[bg];[vo][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
            ROUGH_CUT
        ]
    else:
        print("[INFO] Muxing candidate_3 music track with 9-shot rough cut...")
        cmd = [
            FFMPEG_EXE, "-y",
            "-i", silent_cut,
            "-i", MUSIC_FILE,
            "-filter_complex", "[1:a]volume=0.35,afade=t=in:st=0:d=2,afade=t=out:st=69:d=3[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
            ROUGH_CUT
        ]

    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"\n[DONE] Phase 2 Rough Cut saved to: {ROUGH_CUT}")

if __name__ == "__main__":
    write_docs()
    build_rough_cut()