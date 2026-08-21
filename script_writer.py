"""
script_writer.py

Given a raw trending topic, this:
  1. Turns it into a specific, shootable video angle + target audience + tone
  2. Outlines the video beat by beat
  3. Expands the outline into a full script (visuals + spoken lines)
  4. Polishes the script for hook strength and pacing

Uses Groq's free, no-credit-card API (OpenAI-compatible endpoint) running
openai/gpt-oss-120b. Returns a dict ready to hand to voice_gen.py / image_gen.py /
video_builder.py.
"""

import os
import sys
import json
import requests

GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _call_groq(api_key: str, prompt: str, temperature: float = 0.9, json_mode: bool = False) -> str:
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 2048,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Groq API error {resp.status_code}: {resp.text}")

    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def define_angle(api_key: str, trend_title: str, news_context: str = "") -> dict:
    prompt = f"""You are a viral short-form video strategist for a Tech & AI channel.

A topic is trending right now: "{trend_title}"
{f'Related context: {news_context}' if news_context else ''}

Come up with ONE specific, engaging YouTube Shorts angle that connects this
trend to Tech & AI (e.g. the technology behind it, an AI tool related to it,
a tech industry angle, or a broader tech implication). The video must end up
squarely in the Tech & AI niche - if the trend itself isn't tech-related,
find a genuine tech/AI angle on it rather than ignoring the niche. Keep it
genuinely interesting (not clickbait-empty, not misinformation): an explainer,
a surprising fact, a reaction, or a useful takeaway.

Return ONLY valid JSON, no markdown fences, in this exact shape:
{{
  "video_title": "short punchy title for the video, under 60 characters",
  "angle": "one sentence describing the specific angle/hook",
  "audience": "one line describing who this is for",
  "tone": "one of: conversational, educational, energetic, dramatic, funny"
}}"""
    raw = _call_groq(api_key, prompt, temperature=0.9, json_mode=True)
    return json.loads(raw)


def build_outline(api_key: str, video_title, angle, audience, tone, duration=50):
    prompt = f"""You are a professional video scriptwriter.

Create a beat-by-beat OUTLINE for a YouTube Shorts video.

Title: {video_title}
Angle: {angle}
Audience: {audience}
Tone: {tone}
Target length: {duration} seconds

Numbered list of beats, each with timestamp range, what happens, and its purpose.
First beat = hook in the first 2-3 seconds. Last beat = clear call to action.

Return only the outline."""
    return _call_groq(api_key, prompt, temperature=0.9)


def expand_script(api_key: str, video_title, audience, tone, duration, outline):
    max_words = int(duration * 2.3)  # ~2.3 words/sec natural spoken pace, biased safe
    prompt = f"""You are a professional video scriptwriter.

Using this outline, write the FULL script for a YouTube Shorts video.

Title: {video_title}
Audience: {audience}
Tone: {tone}
Target length: {duration} seconds
HARD LIMIT: the total spoken words across the entire script must be under
{max_words} words. This is a strict constraint, not a suggestion — if the
outline has too much content, cut material rather than exceed the word
limit. Going over will make the video too long.

OUTLINE:
{outline}

For each beat write:
[Timestamp]
VISUAL: one-sentence description of what image/scene should show
SCRIPT: the exact words to say, natural spoken language

Return only the formatted script."""
    return _call_groq(api_key, prompt, temperature=0.9)


def polish_script(api_key: str, video_title, tone, script):
    prompt = f"""You are a script doctor. Review and tighten this script before filming.

TITLE: {video_title}
TONE: {tone}

SCRIPT:
{script}

- Strengthen the hook in the first 2-3 seconds if needed.
- Tighten rambling lines.
- Keep tone consistent.
- Make sure the CTA at the end is clear.

Return the FINAL script in the same [Timestamp] / VISUAL / SCRIPT format only."""
    return _call_groq(api_key, prompt, temperature=0.7)


def generate_full_package(api_key: str, trend_title: str, news_context: str = "", duration: int = 50) -> dict:
    angle_data = define_angle(api_key, trend_title, news_context)
    outline = build_outline(
        api_key, angle_data["video_title"], angle_data["angle"],
        angle_data["audience"], angle_data["tone"], duration,
    )
    script = expand_script(
        api_key, angle_data["video_title"], angle_data["audience"],
        angle_data["tone"], duration, outline,
    )
    final_script = polish_script(api_key, angle_data["video_title"], angle_data["tone"], script)

    return {
        "video_title": angle_data["video_title"],
        "angle": angle_data["angle"],
        "audience": angle_data["audience"],
        "tone": angle_data["tone"],
        "duration": duration,
        "script": final_script,
    }


if __name__ == "__main__":
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        print("Set GROQ_API_KEY first.", file=sys.stderr)
        sys.exit(1)
    pkg = generate_full_package(key, "Example trending topic")
    print(json.dumps(pkg, indent=2))
