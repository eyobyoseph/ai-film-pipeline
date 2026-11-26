import os
import json
import time
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def log_run(stage, provider, model, latency_sec, status, detail=""):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "provider": provider,
        "model": model,
        "latency_sec": round(latency_sec, 2),
        "status": status,
        "detail": detail
    }
    with open("runs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[{status.upper()}] {provider} ({model}) - {latency_sec:.2f}s {detail}")

def test_gemini_with_fallback():
    models = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]
    payload = {"contents": [{"parts": [{"text": "Reply with one Amharic greeting word."}]}]}

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        for attempt in range(1, 3):
            start = time.time()
            try:
                resp = requests.post(url, json=payload, timeout=30)
                latency = time.time() - start
                if resp.status_code == 200:
                    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    log_run("smoke_test", "google_ai_studio", model, latency, "ok", f"(attempt {attempt}) -> {text}")
                    return
                else:
                    log_run("smoke_test", "google_ai_studio", model, latency, "retry_or_fallback", f"HTTP {resp.status_code}")
                    time.sleep(2)
            except Exception as e:
                log_run("smoke_test", "google_ai_studio", model, time.time() - start, "error", str(e))

if __name__ == "__main__":
    test_gemini_with_fallback()