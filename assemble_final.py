import os
import json
import subprocess
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "outputs")
VID_DIR = os.path.join(OUT_DIR, "videos")
TEMP_DIR = os.path.join(OUT_DIR, "temp_final")
os.makedirs(TEMP_DIR, exist_ok=True)

STORYBOARD_PATH = os.path.join(BASE_DIR, "storyboard.json")
import glob; NARRATION_PATH = glob.glob(os.path.join(OUT_DIR, "**", "narration_full.wav"), recursive=True)[0]
MUSIC_PATH = os.path.join(OUT_DIR, "music_candidates", "candidate_3_minimal_ambient_marimba.wav")
SRT_PATH = os.path.join(OUT_DIR, "subtitles.srt")

FINAL_9x16 = os.path.join(OUT_DIR, "final_9x16.mp4")
FINAL_16x9 = os.path.join(OUT_DIR, "final_16x9.mp4")


def format_srt_time(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def build_subtitles(shots):
    cursor = 0.0
    lines = []
    for idx, s in enumerate(shots, start=1):
        dur = float(s.get("duration_sec", 8.0))
        start_t = cursor + 0.25
        end_t = cursor + dur - 0.25
        text = s.get("subtitle_en", "").strip()
        if text:
            lines.append(f"{idx}")
            lines.append(f"{format_srt_time(start_t)} --> {format_srt_time(end_t)}")
            lines.append(text)
            lines.append("")
        cursor += dur

    with open(SRT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[OK] Generated subtitles from storyboard.json -> {SRT_PATH}")
    return cursor


def load_font(size: int, prefer_geez: bool = False):
    candidates = (
        ["C:/Windows/Fonts/ebrima.ttf", "C:/Windows/Fonts/nyala.ttf", "C:/Windows/Fonts/arial.ttf"]
        if prefer_geez
        else ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"]
    )
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def create_end_card_image(width: int, height: int, out_png: str):
    img = Image.new("RGB", (width, height), color=(18, 22, 30))
    draw = ImageDraw.Draw(img)

    # Subtle warm gold accent border
    margin = int(min(width, height) * 0.06)
    draw.rectangle(
        [margin, margin, width - margin, height - margin],
        outline=(212, 175, 55),
        width=3,
    )

    is_vertical = height > width
    f_amharic = load_font(46 if is_vertical else 54, prefer_geez=True)
    f_english = load_font(28 if is_vertical else 34, prefer_geez=False)
    f_meta = load_font(22 if is_vertical else 24, prefer_geez=False)

    lines = [
        ("ድር ቢያብር አንበሳ ያስር", f_amharic, (245, 215, 110), 0.34),
        ("When spider webs unite, they can tie up a lion.", f_english, (240, 240, 240), 0.45),
        ("A Story of Dawit & Selam  •  Addis Ababa", f_meta, (185, 195, 210), 0.56),
        ("Created with AI: Keyframes • Wan 2.2 • ACE-Step • Amharic TTS", f_meta, (145, 155, 170), 0.65),
    ]

    for text, font, color, y_ratio in lines:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (width - tw) // 2
        y = int(height * y_ratio)
        draw.text((x, y), text, font=font, fill=color)

    img.save(out_png)


def get_video_duration(path: str) -> float:
    try:
        _, secs = imageio_ffmpeg.count_frames_and_secs(path)
        return float(secs) if secs > 0 else 1.56
    except Exception:
        return 1.56


def render_aspect_ratio(shots, story_dur: float, width: int, height: int, out_path: str, label: str):
    print(f"\n--- Building {label} ({width}x{height}) ---")
    concat_file = os.path.join(TEMP_DIR, f"concat_{label}.txt")
    is_vertical = height > width

    with open(concat_file, "w", encoding="utf-8") as cf:
        for s in shots:
            shot_id = s["shot_id"]
            target_dur = float(s.get("duration_sec", 8.0))
            raw_mp4 = os.path.join(VID_DIR, f"{shot_id}.mp4")
            if not os.path.exists(raw_mp4):
                raise FileNotFoundError(f"Missing video clip: {raw_mp4}")

            raw_dur = max(get_video_duration(raw_mp4), 0.5)
            pts_factor = target_dur / raw_dur
            clip_out = os.path.join(TEMP_DIR, f"{shot_id}_{label}.mp4")

            if is_vertical:
                vf = (
                    f"setpts={pts_factor:.4f}*PTS,"
                    f"scale={width}:{height}:flags=lanczos,"
                    f"fps=24,format=yuv420p"
                )
            else:
                # 16:9 widescreen: blurred background fill + sharp centered 9:16 frame
                vf = (
                    f"setpts={pts_factor:.4f}*PTS,fps=24,split=2[bg][fg];"
                    f"[bg]scale={width}:{height}:force_original_aspect_ratio=increase,"
                    f"crop={width}:{height},boxblur=25:5[bg_blur];"
                    f"[fg]scale=-2:{height}:flags=lanczos[fg_scaled];"
                    f"[bg_blur][fg_scaled]overlay=(W-w)/2:(H-h)/2,format=yuv420p"
                )

            subprocess.run(
                [
                    FFMPEG_EXE, "-y", "-i", raw_mp4,
                    "-vf", vf,
                    "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                    clip_out,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            cf.write(f"file '{clip_out.replace(chr(92), '/')}'\n")

        # 4-second end card clip
        end_png = os.path.join(TEMP_DIR, f"end_card_{label}.png")
        end_mp4 = os.path.join(TEMP_DIR, f"end_card_{label}.mp4")
        create_end_card_image(width, height, end_png)
        subprocess.run(
            [
                FFMPEG_EXE, "-y", "-loop", "1", "-i", end_png,
                "-t", "4.0",
                "-vf", "fade=t=in:st=0:d=0.6,fps=24,format=yuv420p",
                "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                end_mp4,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        cf.write(f"file '{end_mp4.replace(chr(92), '/')}'\n")

    stitched_silent = os.path.join(TEMP_DIR, f"stitched_{label}.mp4")
    subprocess.run(
        [FFMPEG_EXE, "-y", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", stitched_silent],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    total_dur = story_dur + 4.0
    font_size = 16 if is_vertical else 20
    margin_v = 48 if is_vertical else 28

    # Filter chain:
    # 1. Burn in SRT subtitles
    # 2. Pad narration to total_dur so sidechain ducking works cleanly across the end card
    # 3. Sidechain-duck the marimba score under the narration, swell gently during end card
    # 4. Normalize loudness to -16 LUFS (EBU R128)
    filter_complex = (
        f"[0:v]subtitles=outputs/subtitles.srt:force_style='"
        f"FontName=Arial,FontSize={font_size},PrimaryColour=&H00FFFFFF,"
        f"OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=3,Outline=1,MarginV={margin_v}'[vout];"
        f"[1:a]apad=whole_dur={total_dur:.2f},asplit=2[vo_mix][vo_sc];"
        f"[2:a]volume=0.42,afade=t=in:st=0:d=1.5,afade=t=out:st={total_dur - 2.5:.2f}:d=2.5[music_base];"
        f"[music_base][vo_sc]sidechaincompress=threshold=0.02:ratio=6:attack=40:release=350[music_ducked];"
        f"[vo_mix][music_ducked]amix=inputs=2:duration=first:normalize=0,"
        f"loudnorm=I=-16:TP=-1.5:LRA=11[aout]"
    )

    subprocess.run(
        [
            FFMPEG_EXE, "-y",
            "-i", stitched_silent,
            "-i", NARRATION_PATH,
            "-i", MUSIC_PATH,
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", "[aout]",
            "-t", f"{total_dur:.2f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            out_path,
        ],
        cwd=BASE_DIR,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"[DONE] Exported {out_path} ({total_dur:.1f}s, -16 LUFS normalized)")


def main():
    assert os.path.exists(STORYBOARD_PATH), "Missing storyboard.json"
    assert os.path.exists(NARRATION_PATH), "Missing outputs/narration_full.wav"
    assert os.path.exists(MUSIC_PATH), "Missing candidate_3_minimal_ambient_marimba.wav"

    with open(STORYBOARD_PATH, "r", encoding="utf-8") as f:
        sb = json.load(f)
    shots = sb["shots"]

    story_dur = build_subtitles(shots)
    render_aspect_ratio(shots, story_dur, 720, 1280, FINAL_9x16, "9x16")
    render_aspect_ratio(shots, story_dur, 1280, 720, FINAL_16x9, "16x9")
    print("\n[ALL DONE] Step 1 complete! Check outputs/final_9x16.mp4 and outputs/final_16x9.mp4.")


if __name__ == "__main__":
    main()