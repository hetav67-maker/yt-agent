"""
image_gen.py

Generates one AI image per visual beat using Pollinations.ai's free,
keyless image generation endpoint. Images are generated at vertical
(9:16) resolution to fit YouTube Shorts.
"""

import os
import time
import urllib.parse
import requests

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"
WIDTH, HEIGHT = 1080, 1920


def generate_image(prompt: str, out_path: str, seed: int = None, retries: int = 3) -> str:
    """Download one AI-generated image for the given prompt. Returns out_path."""
    encoded = urllib.parse.quote(prompt[:400])
    url = POLLINATIONS_URL.format(prompt=encoded)
    params = {"width": WIDTH, "height": HEIGHT, "nologo": "true"}
    if seed is not None:
        params["seed"] = seed

    last_err = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=60)
            resp.raise_for_status()
            with open(out_path, "wb") as f:
                f.write(resp.content)
            return out_path
        except requests.RequestException as e:
            last_err = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Failed to generate image after {retries} attempts: {last_err}")


def generate_images_for_scenes(visual_prompts: list[str], out_dir: str, style_suffix: str = "") -> list[str]:
    """Generate one image per visual beat description. Returns list of file paths in order."""
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for i, prompt in enumerate(visual_prompts):
        full_prompt = f"{prompt}, {style_suffix}" if style_suffix else prompt
        out_path = os.path.join(out_dir, f"scene_{i:02d}.jpg")
        generate_image(full_prompt, out_path, seed=i)
        paths.append(out_path)
    return paths


if __name__ == "__main__":
    p = generate_image("a sunrise over mountains, cinematic", "/tmp/test_scene.jpg")
    print(f"Saved to {p}")
