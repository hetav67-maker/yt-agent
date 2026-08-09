"""
main.py

Runs the pipeline end to end:
  1. Find a trending topic
  2. Turn it into a video concept + full script (Groq)
  3. Generate a voiceover
  4. Generate matching AI images
  5. Assemble a finished vertical video

The finished video is saved to ./output/ (not uploaded anywhere) so you can
download it and post it yourself, wherever you like.
"""

import os
import sys
import json
import tempfile
import traceback
from datetime import datetime, timezone

from trend_finder import pick_topic
from script_writer import generate_full_package
from voice_gen import generate_voiceover, extract_visual_prompts
from image_gen import generate_images_for_scenes
from video_builder import build_video

REQUIRED_ENV = ["GROQ_API_KEY"]
OUTPUT_DIR = os.path.join(os.getcwd(), "output")


def check_env():
    missing = [v for v in REQUIRED_ENV if not os.environ.get(v)]
    if missing:
        print(f"[ERROR] Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)


def run_pipeline():
    check_env()
    groq_key = os.environ["GROQ_API_KEY"]
    work_dir = tempfile.mkdtemp(prefix="yt_agent_")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Working directory: {work_dir}")

    try:
        print("\n[1/5] Finding a trending topic...")
        trend = pick_topic()
        print(f"  -> {trend['title']}")

        print("\n[2/5] Writing script...")
        pkg = generate_full_package(groq_key, trend["title"], trend.get("news_snippet", ""))
        print(f"  -> Title: {pkg['video_title']}")

        print("\n[3/5] Generating voiceover...")
        voice_path = os.path.join(work_dir, "voiceover.mp3")
        generate_voiceover(pkg["script"], voice_path)

        print("\n[4/5] Generating scene images...")
        visual_prompts = extract_visual_prompts(pkg["script"])
        if not visual_prompts:
            visual_prompts = [pkg["angle"]]
        image_dir = os.path.join(work_dir, "images")
        image_paths = generate_images_for_scenes(
            visual_prompts, image_dir, style_suffix="cinematic, high detail, vertical composition"
        )

        print("\n[5/5] Assembling video...")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c if c.isalnum() else "_" for c in pkg["video_title"])[:50]
        video_filename = f"{timestamp}_{safe_title}.mp4"
        video_path = os.path.join(OUTPUT_DIR, video_filename)
        build_video(image_paths, voice_path, video_path, title_text=pkg["video_title"])

        info_path = os.path.join(OUTPUT_DIR, f"{timestamp}_{safe_title}.json")
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(pkg, f, indent=2)

        caption_path = os.path.join(OUTPUT_DIR, f"{timestamp}_{safe_title}_TITLE_AND_DESCRIPTION.txt")
        description = (
            f"{pkg['angle']}\n\n"
            f"{'Follow for more Tech & AI in under a minute.'}\n\n"
            f"#tech #ai #shorts #technology #artificialintelligence"
        )
        with open(caption_path, "w", encoding="utf-8") as f:
            f.write("TITLE (copy-paste this):\n")
            f.write(pkg["video_title"] + "\n\n")
            f.write("DESCRIPTION (copy-paste this):\n")
            f.write(description + "\n")

        print(f"\nDone. Video saved to: {video_path}")
        print(f"Script/metadata saved to: {info_path}")
        print(f"Title/description saved to: {caption_path}")
        print("Download it all from the GitHub Actions run's 'Artifacts' section, then upload it yourself.")

    except Exception:
        print("\n[PIPELINE FAILED]", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()
