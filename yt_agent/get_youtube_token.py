"""
get_youtube_token.py

RUN THIS ONCE, LOCALLY ON YOUR COMPUTER (not in GitHub Actions).

It opens a browser window asking you to log in to the Google account that
owns your YouTube channel and approve upload access. It then prints a
refresh token - copy that into your .env / GitHub secrets as
YOUTUBE_REFRESH_TOKEN and you never need to run this again.

Prerequisites:
  1. Go to https://console.cloud.google.com/
  2. Create a project (or use an existing one)
  3. Enable the "YouTube Data API v3" (APIs & Services -> Library)
  4. Configure the OAuth consent screen (External, add your own email as a test user)
  5. Create OAuth credentials: APIs & Services -> Credentials -> Create Credentials
     -> OAuth client ID -> Application type: "Desktop app"
  6. Copy the Client ID and Client Secret it gives you and paste below or set
     as env vars YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET before running this.
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    client_id = os.environ.get("YOUTUBE_CLIENT_ID") or input("Paste your OAuth Client ID: ").strip()
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET") or input("Paste your OAuth Client Secret: ").strip()

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n" + "=" * 60)
    print("SUCCESS. Save these as environment variables / GitHub secrets:")
    print("=" * 60)
    print(f"YOUTUBE_CLIENT_ID={client_id}")
    print(f"YOUTUBE_CLIENT_SECRET={client_secret}")
    print(f"YOUTUBE_REFRESH_TOKEN={creds.refresh_token}")
    print("=" * 60)


if __name__ == "__main__":
    main()
