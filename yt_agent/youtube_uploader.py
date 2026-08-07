"""
youtube_uploader.py

Uploads a finished video to YouTube using the Data API v3, authenticating
with a long-lived refresh token (generated once via get_youtube_token.py).
"""

import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_authenticated_service():
    client_id = os.environ["YOUTUBE_CLIENT_ID"]
    client_secret = os.environ["YOUTUBE_CLIENT_SECRET"]
    refresh_token = os.environ["YOUTUBE_REFRESH_TOKEN"]

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    return build("youtube", "v3", credentials=creds)


def upload_short(video_path: str, title: str, description: str, tags: list[str] = None) -> str:
    """Upload a video as a YouTube Short. Returns the resulting video ID."""
    youtube = get_authenticated_service()

    body = {
        "snippet": {
            "title": title[:100],
            "description": f"{description}\n\n#shorts",
            "tags": tags or [],
            "categoryId": "22",  # People & Blogs; adjust if you want a different default
        },
        "status": {
            "privacyStatus": "public",  # change to "private" or "unlisted" while testing
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"Uploaded: https://youtube.com/shorts/{video_id}")
    return video_id


if __name__ == "__main__":
    print("Run via main.py after a video has been built.")
