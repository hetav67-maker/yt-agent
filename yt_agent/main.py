"""
main.py

Runs the full pipeline end to end:
  1. Find a trending topic (free Google Trends RSS)
  2. Turn it into a video concept + full script (Gemini)
  3. Generate a voiceover (free edge-tts)
  4. Generate matching AI images (free Pollinations.ai)
  5. Assemble a finished vertical video (moviepy/ffmpeg)
  6. Upload to YouTube as a Short (YouTube Data API)

Run manually with `python main.py`, or on a schedule via the included
GitHub Actions workflow (.github/workflows/auto_upload.yml), which runs
this every 10 hours.
"""

import os
import sys
import shutil
import tempfile
import traceback

from trend_finder import pick_topic
from script_writer import generate_full_package
from voice_gen import generate_voiceover, extract_visual_prompts
from image_gen import generate_images_for_scenes
from video_builder import build_video
from youtube_uploader import upload_short

REQUIRED_ENV = [
    "GEMINI_API_KEY", "YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN",
]


def check_env():
    missing = [v for v in REQUIRED_ENV if not os.environ.get(v)]
    if missing:
        print(f"[ERROR] Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        print("See .env.example / README.md for setup instructions.", file=sys.stderr)
        sys.exit(1)


def run_pipeline():
    check_env()
    gemini_key = os.environ["GEMINI_API_KEY"]
    work_dir = tempfile.mkdtemp(prefix="yt_agent_")
    print(f"Working directory: {work_dir}")

    try:
        # 1. Trend
        print("\n[1/6] Finding a trending topic...")
        trend = pick_topic()
        print(f"  -> {trend['title']}")

        # 2. Script package
        print("\n[2/6] Writing script (angle, audience, outline, full script, polish)...")
        pkg = generate_full_package(gemini_key, trend["title"], trend.get("news_snippet", ""))
        print(f"  -> Title: {pkg['video_title']}")
        print(f"  -> Audience: {pkg['audience']}")
        print(f"  -> Tone: {pkg['tone']}")

        # 3. Voiceover
        print("\n[3/6] Generating voiceover...")
        voice_path = os.path.join(work_dir, "voiceover.mp3")
        generate_voiceover(pkg["script"], voice_path)
        print(f"  -> {voice_path}")

        # 4. Images
        print("\n[4/6] Generating scene images...")
        visual_prompts = extract_visual_prompts(pkg["script"])
        if not visual_prompts:
            visual_prompts = [pkg["angle"]]  # fallback: one generic scene
        image_dir = os.path.join(work_dir, "images")
        image_paths = generate_images_for_scenes(
            visual_prompts, image_dir, style_suffix="cinematic, high detail, vertical composition"
        )
        print(f"  -> {len(image_paths)} images generated")

        # 5. Assemble video
        print("\n[5/6] Assembling video...")
        video_path = os.path.join(work_dir, "final_video.mp4")
        build_video(image_paths, voice_path, video_path, title_text=pkg["video_title"])
        print(f"  -> {video_path}")

        # 6. Upload
        print("\n[6/6] Uploading to YouTube...")
        video_id = upload_short(
            video_path,
            title=pkg["video_title"],
            description=f"{pkg['angle']}\n\nTarget audience: {pkg['audience']}",
        )
        print(f"\nDone. https://youtube.com/shorts/{video_id}")

    except Exception:
        print("\n[PIPELINE FAILED]", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
    finally:
        # comment this out if you want to inspect generated assets afterward
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    run_pipeline()
