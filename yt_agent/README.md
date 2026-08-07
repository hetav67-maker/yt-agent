# Auto YouTube Shorts Agent

Finds a trending topic → writes a script → generates voiceover + AI images →
assembles a video → uploads it as a YouTube Short. Runs automatically every
10 hours via GitHub Actions, for free.

## What's free and what isn't

| Step | Tool | Cost |
|---|---|---|
| Trend discovery | Google Trends RSS | Free, no key |
| Script writing | Gemini API (`gemini-2.0-flash`) | Free tier (~1,500 requests/day) |
| Voiceover | edge-tts | Free, no key |
| Images | Pollinations.ai | Free, no key |
| Video assembly | ffmpeg / moviepy | Free, open source |
| Upload | YouTube Data API | Free quota (~6 uploads/day) |
| Scheduling | GitHub Actions | Free (public repo, or 2,000 min/month private) |

Nothing in this pipeline requires a paid API. The trade-off for "free" is that
image/voice quality is simpler than a paid AI video generator (Veo, Runway) -
this makes slideshow-style narrated Shorts, not fully animated AI video.

## One-time setup (about 15 minutes)

### 1. Get a Gemini API key
Go to https://aistudio.google.com/apikey → Create API key. No card needed.

### 2. Set up YouTube upload access
1. Go to https://console.cloud.google.com/ and create a project.
2. **APIs & Services → Library** → enable "YouTube Data API v3".
3. **APIs & Services → OAuth consent screen** → choose "External" → fill in
   the required fields → add your own Google account email under "Test users".
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID**
   → Application type: **Desktop app** → note the Client ID and Client Secret.
5. On your own computer (this step needs a real browser, so it can't run in
   GitHub Actions): install Python, then:
   ```bash
   pip install google-auth-oauthlib
   export YOUTUBE_CLIENT_ID="your-client-id"
   export YOUTUBE_CLIENT_SECRET="your-client-secret"
   python get_youtube_token.py
   ```
   This opens a browser, asks you to approve upload access to your channel,
   and prints a `YOUTUBE_REFRESH_TOKEN`. Save all three values.

### 3. Put this code in a GitHub repo
1. Create a new repo (public is fine and keeps Actions minutes unlimited-free;
   private also works within the free monthly minutes).
2. Push this folder's contents to it.

### 4. Add your secrets to GitHub
Repo → **Settings → Secrets and variables → Actions → New repository secret**.
Add all four:
- `GEMINI_API_KEY`
- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`

### 5. Done
The workflow in `.github/workflows/auto_upload.yml` runs every 10 hours
automatically. You can also trigger it manually anytime from the repo's
**Actions** tab → "Auto-generate and upload YouTube Short" → **Run workflow**.

## Running it locally (to test before automating)

```bash
pip install -r requirements.txt
# also install ffmpeg and imagemagick on your system (e.g. `brew install ffmpeg imagemagick`
# on Mac, or `sudo apt install ffmpeg imagemagick` on Linux)

export GEMINI_API_KEY="..."
export YOUTUBE_CLIENT_ID="..."
export YOUTUBE_CLIENT_SECRET="..."
export YOUTUBE_REFRESH_TOKEN="..."

python main.py
```

## Strongly recommended before letting it run unattended

- In `youtube_uploader.py`, the upload defaults to `"privacyStatus": "public"`.
  **Change it to `"private"` or `"unlisted"` for your first several runs**
  so you can review what it's producing before it's publicly live on autopilot.
- Trending topics are picked automatically and can occasionally be about
  sensitive news events. Consider reviewing videos before making them public,
  or adding a keyword blocklist in `trend_finder.py` if certain topics should
  be skipped.
- YouTube's default upload quota is ~6/day; every-10-hours (2.4/day) comfortably
  fits, but don't lower the interval much further without requesting a quota
  increase from Google.
