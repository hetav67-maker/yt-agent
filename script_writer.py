"""
script_writer.py

Given a raw trending topic, this:
1. Turns it into a specific, shootable video angle + target audience + tone
2. Outlines the video beat by beat
3. Expands the outline into a full script (visuals + spoken lines)
4. Polishes the script for hook strength and pacing

Uses Groq's free, no-credit-card API (OpenAI-compatible endpoint) running
Llama 3.3 70B. Returns a dict ready to hand to voice_gen.py / image_gen.py /
video_builder.py.
"""

import os
import sys
import json
import time
import requests

GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Groq deprecated llama-3.3-70b-versatile (sunset Aug 2026); openai/gpt-oss-120b
# is their recommended replacement. Free tier is 8000 tokens/minute. Keep
# per-call requests modest and add a gap between the 4 sequential calls in
# generate_full_package so their token usage doesn't stack up inside the
# same rolling 60s window.
DEFAULT_MAX_TOKENS = 1024
INTER_CALL_DELAY_SECONDS = 12
MAX_RETRIES = 5


def _call_groq(api_key: str, prompt: str, temperature: float = 0.9,
                json_mode: bool = False, max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    for attempt in range(1, MAX_RETRIES + 1):
        resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=60)

        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

        if resp.status_code == 429 and attempt < MAX_RETRIES:
            wait = _seconds_to_wait(resp, default=5 * attempt)
            print(f"  [rate limited] attempt {attempt}/{MAX_RETRIES}, "
                  f"waiting {wait:.1f}s before retry...", file=sys.stderr)
            time.sleep(wait)
            continue

        raise RuntimeError(f"Groq API error {resp.status_code}: {resp.text}")

    raise RuntimeError("Groq API error: exhausted retries on rate limit (429)")


def _seconds_to_wait(resp, default: float) -> float:
    """Prefer the Retry-After header; fall back to parsing Groq's error text
    (e.g. '...Please try again in 2.9175s...'); fall back to `default`."""
    retry_after = resp.headers.get("retry-after")
    if retry_after:
        try:
            return float(retry_after) + 0.5
        except ValueError:
            pass
    try:
        body = resp.json()
        msg = body.get("error", {}).get("message", "")
        if "try again in" in msg:
            frag = msg.split("try again in", 1)[1].strip()
            num = "".join(c for c in frag.split("s", 1)[0] if c.isdigit() or c == ".")
            if num:
                return float(num) + 0.5
    except Exception:
        pass
    return default


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
    raw = _call_groq(api_key, prompt, temperature=0.9, json_mode=True, max_tokens=400)
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
    return _call_groq(api_key, prompt, temperature=0.9, max_tokens=600)


def expand_script(api_key: str, video_title, audience, tone, duration, outline):
    prompt = f"""You are a professional video scriptwriter.

Using this outline, write the FULL script for a YouTube Shorts video.

Title: {video_title}
Audience: {audience}
Tone: {tone}
Target length: {duration} seconds

OUTLINE:
{outline}

For each beat write:
[Timestamp]
VISUAL: one-sentence description of what image/scene should show
SCRIPT: the exact words to say, natural spoken language

Return only the formatted script."""
    return _call_groq(api_key, prompt, temperature=0.9, max_tokens=1024)


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
    return _call_groq(api_key, prompt, temperature=0.7, max_tokens=1024)


def generate_full_package(api_key: str, trend_title: str, news_context: str = "", duration: int = 50) -> dict:
    angle_data = define_angle(api_key, trend_title, news_context)
    time.sleep(INTER_CALL_DELAY_SECONDS)

    outline = build_outline(
        api_key, angle_data["video_title"], angle_data["angle"],
        angle_data["audience"], angle_data["tone"], duration,
    )
    time.sleep(INTER_CALL_DELAY_SECONDS)

    script = expand_script(
        api_key, angle_data["video_title"], angle_data["audience"],
        angle_data["tone"], duration, outline,
    )
    time.sleep(INTER_CALL_DELAY_SECONDS)

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
