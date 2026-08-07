"""
voice_gen.py

Extracts the spoken lines from the formatted script and synthesizes a
voiceover using edge-tts (Microsoft Edge's free, keyless TTS engine).
"""

import re
import asyncio
import edge_tts

DEFAULT_VOICE = "en-US-AndrewNeural"  # natural-sounding free voice; browse more with `edge-tts --list-voices`


def extract_spoken_lines(script: str) -> list[str]:
    """Pull out just the 'SCRIPT:' lines from the beat-formatted script text."""
    lines = []
    for raw_line in script.splitlines():
        m = re.match(r"\s*SCRIPT:\s*(.+)", raw_line, re.IGNORECASE)
        if m:
            lines.append(m.group(1).strip())
    return lines


def extract_visual_prompts(script: str) -> list[str]:
    """Pull out the 'VISUAL:' lines - used later to generate matching images."""
    lines = []
    for raw_line in script.splitlines():
        m = re.match(r"\s*VISUAL:\s*(.+)", raw_line, re.IGNORECASE)
        if m:
            lines.append(m.group(1).strip())
    return lines


async def _synthesize(text: str, out_path: str, voice: str = DEFAULT_VOICE):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_path)


def generate_voiceover(script: str, out_path: str, voice: str = DEFAULT_VOICE) -> str:
    """Synthesize the full voiceover as a single mp3 file. Returns the path."""
    lines = extract_spoken_lines(script)
    full_text = " ".join(lines) if lines else script  # fallback: read whole script
    asyncio.run(_synthesize(full_text, out_path, voice))
    return out_path


if __name__ == "__main__":
    sample = """[0:00-0:03]
VISUAL: close up shot, dramatic lighting
SCRIPT: Did you know this one habit changes everything?

[0:03-0:08]
VISUAL: b-roll of a morning routine
SCRIPT: Here's what top performers do differently every single day."""
    print(extract_spoken_lines(sample))
    print(extract_visual_prompts(sample))
