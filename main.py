"""
main.py

Runs the full pipeline end to end:
  1. Find a trending topic
  2. Turn it into a video concept + full script (Gemini)
  3. Generate a voiceover
  4. Generate matching AI images
  5. Assemble a finished vertical video
  6. Upload to Instagram as a Reel
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
from instagram_uploader import upload_reel

REQUIRED_ENV = [
    "GEMINI_API_KEY", "INSTAGRAM_USER_ID", "INSTAGRAM_ACCESS_TOKEN",
]


def check_env():
    missing = [v for v in REQUIRED_ENV if not os.environ.get(v)]
    if missing:
        print(f"[ERROR] Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)


def run_pipeline():
    check_env()
    gemini_key = os.environ["GEMINI_API_KEY"]
    work_dir = tempfile.mkdtemp(prefix="yt_agent_")
    print(f"Working directory: {work_dir}")

    try:
        print("\n[1/6] Finding a trending topic...")
        trend = pick_topic()
        print(f"  -> {trend['title']}")

        print("\n[2/6] Writing script...")
        pkg = generate_full_package(gemini_key, trend["title"], trend.get("news_snippet", ""))
        print(f"  -> Title: {pkg['video_title']}")

        print("\n[3/6] Generating voiceover...")
        voice_path = os.path.join(work_dir, "voiceover.mp3")
        generate_voiceover(pkg["script"], voice_path)

        print("\n[4/6] Generating scene images...")
        visual_prompts = extract_visual_prompts(pkg["script"])
        if not visual_prompts:
            visual_prompts = [pkg["angle"]]
        image_dir = os.path.join(work_dir, "images")
        image_paths = generate_images_for_scenes(
            visual_prompts, image_dir, style_suffix="cinematic, high detail, vertical composition"
        )

        print("\n[5/6] Assembling video...")
        video_path = os.path.join(work_dir, "final_video.mp4")
        build_video(image_paths, voice_path, video_path, title_text=pkg["video_title"])

        print("\n[6/6] Uploading to Instagram...")
        caption = f"{pkg['video_title']}\n\n{pkg['angle']}\n\n#reels #shorts"
        media_id = upload_reel(video_path, caption)
        print(f"\nDone. Published Instagram media ID: {media_id}")

    except Exception:
        print("\n[PIPELINE FAILED]", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    run_pipeline()
