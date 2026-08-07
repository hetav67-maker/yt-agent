"""
video_builder.py

Stitches the voiceover audio + generated images into a finished vertical
(1080x1920) video for YouTube Shorts, with a simple Ken Burns zoom and a
title card at the start.
"""

from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeVideoClip, TextClip, concatenate_videoclips
)

W, H = 1080, 1920


def _ken_burns_clip(image_path: str, duration: float, zoom_start=1.0, zoom_end=1.12):
    """A slow zoom-in on a still image, moviepy-native (no extra deps)."""
    clip = ImageClip(image_path).set_duration(duration)
    clip = clip.resize(height=H).resize(lambda t: zoom_start + (zoom_end - zoom_start) * (t / duration))
    clip = clip.set_position("center")
    return CompositeVideoClip([clip], size=(W, H)).set_duration(duration)


def build_video(
    image_paths: list[str],
    voiceover_path: str,
    out_path: str,
    title_text: str = None,
    title_duration: float = 2.5,
) -> str:
    """
    Combine images (evenly split across the voiceover's duration) and the
    voiceover audio into a finished mp4. Optionally overlays a title card
    for the first couple of seconds.
    """
    audio = AudioFileClip(voiceover_path)
    total_duration = audio.duration

    if not image_paths:
        raise ValueError("No images provided to build_video().")

    per_image = total_duration / len(image_paths)
    scene_clips = [_ken_burns_clip(p, per_image) for p in image_paths]
    video = concatenate_videoclips(scene_clips, method="compose").set_audio(audio)

    if title_text:
        try:
            title_clip = (
                TextClip(title_text, fontsize=64, color="white", font="DejaVu-Sans-Bold",
                         size=(W - 120, None), method="caption")
                .set_position("center")
                .set_duration(min(title_duration, total_duration))
                .on_color(size=(W, H), color=(0, 0, 0), col_opacity=0.35)
            )
            video = CompositeVideoClip([video, title_clip])
        except Exception:
            # ImageMagick/font issues shouldn't kill the whole pipeline - skip the title card.
            pass

    video.write_videofile(
        out_path, fps=30, codec="libx264", audio_codec="aac",
        preset="medium", threads=4, logger=None,
    )
    return out_path


if __name__ == "__main__":
    print("This module is meant to be called from main.py with real assets.")
