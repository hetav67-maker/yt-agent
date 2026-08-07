"""
voice_gen.py

Extracts the spoken lines from the formatted script and synthesizes a
voiceover using edge-tts (Microsoft Edge's free, keyless TTS engine).
"""

import re
import asyncio
import edge_tts

DEFAULT_VOICE = "en-US-AndrewNeural"


def extract_spoken_lines(script: str) -> list[str]:
    lines = []
    for raw_line in script.splitlines():
        m = re.match(r"\s*SCRIPT:\s*(.+)", raw_line, re.IGNORECASE)
        if m:
            lines.append(m.group(1).strip())
    return lines


def extract_visual_prompts(script: str) -> list[str]:
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
    lines = extract_spoken_lines(script)
    full_text = " ".join(lines) if lines else script
    asyncio.run(_synthesize(full_text, out_path, voice))
    return out_path
