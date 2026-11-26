import os
import json
import time
import wave
import base64
import asyncio
import subprocess
from datetime import datetime, timezone
import requests
import edge_tts
import imageio_ffmpeg
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

os.makedirs("outputs/audio", exist_ok=True)

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
    print(f"[{status.upper()}] {stage} | {provider}/{model} ({latency_sec:.2f}s) {detail}")

def try_gemini_tts(shot_id, text, out_wav):
    models = ["gemini-2.5-flash-preview-tts", "gemini-3.8-flash"]
    payload = {
        "contents": [{
            "parts": [{"text": f"Read this Amharic narration warmly and naturally:\n{text}"}]
        }],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {"voiceName": "Aoede"}
                }
            }
        }
    }

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        start = time.time()
        try:
            resp = requests.post(url, json=payload, timeout=25)
            latency = time.time() - start
            if resp.status_code == 200:
                parts = resp.json()["candidates"][0]["content"]["parts"]
                for p in parts:
                    if "inlineData" in p:
                        raw_bytes = base64.b64decode(p["inlineData"]["data"])
                        if raw_bytes[:4] == b"RIFF":
                            with open(out_wav, "wb") as f:
                                f.write(raw_bytes)
                        else:
                            with wave.open(out_wav, "wb") as wf:
                                wf.setnchannels(1)
                                wf.setsampwidth(2)
                                wf.setframerate(24000)
                                wf.writeframes(raw_bytes)
                        log_run("tts_narration", "google_ai_studio", model, latency, "ok", f"{shot_id} -> {out_wav}")
                        return True
            log_run("tts_narration", "google_ai_studio", model, latency, "fallback", f"{shot_id} HTTP {resp.status_code}")
        except Exception as e:
            log_run("tts_narration", "google_ai_studio", model, time.time() - start, "fallback", f"{shot_id}: {type(e).__name__}")
    return False

async def _edge_tts_save(text, out_mp3):
    communicate = edge_tts.Communicate(text, voice="am-ET-MekdesNeural", rate="-5%")
    await communicate.save(out_mp3)

def generate_edge_tts_fallback(shot_id, text, out_wav):
    temp_mp3 = f"outputs/audio/{shot_id}_edge.mp3"
    start = time.time()
    asyncio.run(_edge_tts_save(text, temp_mp3))
    subprocess.run([
        FFMPEG, "-y", "-i", temp_mp3, "-ar", "44100", "-ac", "2", out_wav
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    latency = time.time() - start
    log_run("tts_narration", "edge_tts_fallback", "am-ET-MekdesNeural", latency, "ok", f"{shot_id} -> {out_wav}")

def get_wav_duration(wav_path):
    with wave.open(wav_path, "rb") as wf:
        return wf.getnframes() / float(wf.getframerate())

def main():
    with open("storyboard.json", "r", encoding="utf-8") as f:
        sb = json.load(f)

    padded_clips = []
    total_duration = 0.0

    for shot in sb["shots"]:
        shot_id = shot["shot_id"]
        raw_wav = f"outputs/audio/{shot_id}_raw.wav"
        padded_wav = f"outputs/audio/{shot_id}_padded.wav"

        if not try_gemini_tts(shot_id, shot["narration_amharic"], raw_wav):
            generate_edge_tts_fallback(shot_id, shot["narration_amharic"], raw_wav)

        speech_dur = get_wav_duration(raw_wav)
        slot_dur = max(float(shot["duration_sec"]), speech_dur + 0.6)
        total_duration += slot_dur

        subprocess.run([
            FFMPEG, "-y", "-i", raw_wav,
            "-af", f"apad=whole_dur={slot_dur:.2f}",
            "-ar", "44100", "-ac", "2", padded_wav
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        padded_clips.append(padded_wav)

    concat_list = "outputs/audio/concat.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for clip in padded_clips:
            f.write(f"file '{os.path.abspath(clip).replace(os.sep, '/')}'\n")

    narration_full = "outputs/audio/narration_full.wav"
    subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c", "copy", narration_full
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    radio_cut_path = "outputs/radio_cut.mp4"
    music_expr = "0.04*(sin(2*PI*220*t)+0.7*sin(2*PI*277.18*t)+0.5*sin(2*PI*329.63*t))"
    fade_out_start = max(0, total_duration - 3)
    subprocess.run([
        FFMPEG, "-y",
        "-f", "lavfi", "-i", f"color=c=black:s=720x1280:r=24:d={total_duration:.2f}",
        "-i", narration_full,
        "-f", "lavfi", "-i", f"aevalsrc={music_expr}:s=44100:d={total_duration:.2f}",
        "-filter_complex", f"[1:a]volume=1.0[voice];[2:a]afade=t=in:st=0:d=2,afade=t=out:st={fade_out_start:.2f}:d=3[music];[voice][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        radio_cut_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    print(f"\n[DONE] Radio cut assembled successfully: {radio_cut_path} ({total_duration:.1f}s)")

if __name__ == "__main__":
    main()