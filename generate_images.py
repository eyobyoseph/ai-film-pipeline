import os
import json
import time
import base64
import hashlib
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv

load_dotenv()
CF_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CF_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

MODEL = "@cf/black-forest-labs/flux-1-schnell"
URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{MODEL}"
HEADERS = {"Authorization": f"Bearer {CF_API_TOKEN}"}

OUT_DIR = "outputs/images"
CACHE_FILE = "outputs/images/cache_manifest.json"
os.makedirs(OUT_DIR, exist_ok=True)

STYLE_LOCK = (
    "Cinematic realism, warm golden-hour lighting in Addis Ababa Ethiopia, "
    "35mm film photography aesthetic, shallow depth of field, rich natural skin tones, "
    "consistent wardrobe and facial features, 9:16 vertical composition"
)

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

def log_run(stage, model, latency_sec, status, detail=""):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "provider": "cloudflare_workers_ai",
        "model": model,
        "latency_sec": round(latency_sec, 2),
        "status": status,
        "detail": detail
    }
    with open("runs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[{status.upper()}] {stage} ({latency_sec:.2f}s) {detail}")

def generate_cached_image(key_name, prompt, out_path, cache):
    payload = {
        "prompt": prompt,
        "steps": 6
    }
    # Hash exact inputs so unchanged shots are skipped on re-run
    input_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]

    if cache.get(key_name) == input_hash and os.path.exists(out_path):
        print(f"[CACHED] {key_name} -> {out_path} (inputs unchanged, skipped)")
        return True

    start = time.time()
    try:
        resp = requests.post(URL, headers=HEADERS, json=payload, timeout=90)
        latency = time.time() - start
        if resp.status_code == 200:
            img_b64 = resp.json()["result"]["image"]
            with open(out_path, "wb") as f:
                f.write(base64.b64decode(img_b64))
            cache[key_name] = input_hash
            save_cache(cache)
            log_run("image_gen", MODEL, latency, "ok", f"{key_name} -> {out_path}")
            return True
        else:
            log_run("image_gen", MODEL, latency, "error", f"{key_name} HTTP {resp.status_code}: {resp.text[:140]}")
            return False
    except Exception as e:
        log_run("image_gen", MODEL, time.time() - start, "error", f"{key_name}: {e}")
        return False

def build_conditioned_prompt(shot, characters):
    raw_prompt = shot["image_prompt"]
    char_anchors = []
    if "dawit" in raw_prompt.lower():
        char_anchors.append(f"Dawit: {characters['dawit']}")
    if "selam" in raw_prompt.lower():
        char_anchors.append(f"Selam: {characters['selam']}")

    anchor_prefix = ("Character consistency sheet — " + "; ".join(char_anchors) + ". ") if char_anchors else ""
    return f"{anchor_prefix}{raw_prompt}. {STYLE_LOCK}"

def main():
    with open("storyboard.json", "r", encoding="utf-8") as f:
        sb = json.load(f)

    cache = load_cache()
    chars = sb["characters"]

    # 1. Generate Character & Style Reference Sheet first
    ref_prompt = (
        f"Character and visual style reference sheet split into two clean panels: "
        f"Left panel portrait of Dawit ({chars['dawit']}); "
        f"Right panel portrait of Selam ({chars['selam']}). "
        f"Neutral warm library background, clear facial features, front-facing reference sheet. {STYLE_LOCK}"
    )
    ok = generate_cached_image(
        key_name="character_ref_sheet",
        prompt=ref_prompt,
        out_path=f"{OUT_DIR}/character_ref_sheet.png",
        cache=cache
    )
    if not ok:
        print("Failed to generate reference sheet. Check your Cloudflare credentials.")
        return

    # 2. Generate all 9 shot keyframes conditioned on the character & style reference
    for shot in sb["shots"]:
        shot_id = shot["shot_id"]
        conditioned_prompt = build_conditioned_prompt(shot, chars)
        generate_cached_image(
            key_name=shot_id,
            prompt=conditioned_prompt,
            out_path=f"{OUT_DIR}/{shot_id}.png",
            cache=cache
        )
        time.sleep(1)

    print("\n[DONE] Reference sheet + all 9 keyframes ready in outputs/images/")

if __name__ == "__main__":
    main()