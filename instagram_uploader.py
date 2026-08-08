"""
instagram_uploader.py

Uploads a finished video to Instagram as a Reel using the Meta Graph API.
"""

import os
import time
import requests

GRAPH_API_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def _upload_to_temp_host(video_path: str) -> str:
    with open(video_path, "rb") as f:
        resp = requests.post("https://0x0.st", files={"file": f}, timeout=120)
    resp.raise_for_status()
    url = resp.text.strip()
    if not url.startswith("http"):
        raise RuntimeError(f"Unexpected response from temp host: {url}")
    return url


def _create_media_container(ig_user_id: str, access_token: str, video_url: str, caption: str) -> str:
    resp = requests.post(
        f"{GRAPH_BASE}/{ig_user_id}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption[:2200],
            "access_token": access_token,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def _wait_for_container_ready(container_id: str, access_token: str, timeout_s: int = 300) -> None:
    start = time.time()
    while time.time() - start < timeout_s:
        resp = requests.get(
            f"{GRAPH_BASE}/{container_id}",
            params={"fields": "status_code", "access_token": access_token},
            timeout=30,
        )
        resp.raise_for_status()
        status = resp.json().get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError("Instagram failed to process the video container.")
        time.sleep(5)
    raise TimeoutError("Timed out waiting for Instagram to process the video.")


def _publish_container(ig_user_id: str, access_token: str, container_id: str) -> str:
    resp = requests.post(
        f"{GRAPH_BASE}/{ig_user_id}/media_publish",
        data={"creation_id": container_id, "access_token": access_token},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def upload_reel(video_path: str, caption: str) -> str:
    ig_user_id = os.environ["INSTAGRAM_USER_ID"]
    access_token = os.environ["INSTAGRAM_ACCESS_TOKEN"]

    print("  Uploading video to temporary host...")
    video_url = _upload_to_temp_host(video_path)

    print("  Creating media container on Instagram...")
    container_id = _create_media_container(ig_user_id, access_token, video_url, caption)

    print("  Waiting for Instagram to process the video...")
    _wait_for_container_ready(container_id, access_token)

    print("  Publishing...")
    media_id = _publish_container(ig_user_id, access_token, container_id)
    print(f"  Published: media ID {media_id}")
    return media_id
