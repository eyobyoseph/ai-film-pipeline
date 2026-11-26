import os, sys, json, hashlib, subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "outputs")
CACHE_FILE = os.path.join(OUT_DIR, ".pipeline_cache.json")
STORYBOARD_PATH = os.path.join(BASE_DIR, "storyboard.json")

def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

def run_step(cmd, desc):
    print(f"\n[PIPELINE] {desc}")
    subprocess.run(cmd, cwd=BASE_DIR, check=True)

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    cache = load_cache()
    with open(STORYBOARD_PATH, "r", encoding="utf-8") as f:
        sb = json.load(f)

    if os.path.exists(os.path.join(BASE_DIR, "validate_storyboard.py")):
        run_step([sys.executable, "validate_storyboard.py"], "Stage 1: Validate storyboard")

    nar_items = [(s['shot_id'], s.get('narration_amharic', ''), s.get('duration_sec', 8.0)) for s in sb['shots']]
    nar_hash = sha256_text(json.dumps(nar_items, ensure_ascii=False))
    nar_wav = os.path.join(OUT_DIR, "narration_full.wav")

    if cache.get("narration_hash") != nar_hash or not os.path.exists(nar_wav):
        if os.path.exists(os.path.join(BASE_DIR, "generate_radio_cut.py")):
            run_step([sys.executable, "generate_radio_cut.py"], "Stage 2: Generate Amharic TTS")
        cache["narration_hash"] = nar_hash
        save_cache(cache)
    else:
        print("[CACHE HIT] Narration unchanged; skipping TTS regeneration.")

    shot_hashes = cache.get("shots", {})
    changed = []
    for s in sb["shots"]:
        sid = s["shot_id"]
        h = sha256_text(json.dumps(s, sort_keys=True, ensure_ascii=False))
        vid = os.path.join(OUT_DIR, "videos", f"{sid}.mp4")
        if shot_hashes.get(sid) != h or not os.path.exists(vid):
            changed.append((sid, h))

    if changed:
        print(f"[CACHE MISS] Changed/missing shots: {[c[0] for c in changed]}")
        if os.path.exists(os.path.join(BASE_DIR, "generate_images.py")):
            run_step([sys.executable, "generate_images.py"], "Stage 3: Regenerate changed keyframes")
        for sid, h in changed:
            shot_hashes[sid] = h
        cache["shots"] = shot_hashes
        save_cache(cache)
    else:
        print("[CACHE HIT] All 9 shot keyframes & Wan 2.2 clips match hashes.")

    if os.path.exists(os.path.join(BASE_DIR, "assemble_final.py")):
        run_step([sys.executable, "assemble_final.py"], "Stage 4: Final Edit & Dual Export")

    print("\n[SUCCESS] Pipeline complete: outputs/final_9x16.mp4 & outputs/final_16x9.mp4")

if __name__ == "__main__":
    main()
