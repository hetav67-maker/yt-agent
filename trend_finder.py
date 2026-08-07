"""
trend_finder.py

Pulls today's trending searches from Google Trends' free public RSS feed
(no API key required) and picks one as the seed topic for the video.
"""

import random
import requests
import xml.etree.ElementTree as ET

TRENDS_RSS_URL = "https://trends.google.com/trending/rss?geo=US"


def get_trending_topics(limit: int = 10) -> list[dict]:
    """Return a list of {'title': str, 'traffic': str, 'news_snippet': str} dicts."""
    resp = requests.get(TRENDS_RSS_URL, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    ns = {"ht": "https://trends.google.com/trending/rss"}
    items = []

    for item in root.findall(".//item")[:limit]:
        title = item.findtext("title", default="").strip()
        traffic = item.findtext("ht:approx_traffic", default="", namespaces=ns).strip()
        news_title = item.findtext(".//ht:news_item_title", default="", namespaces=ns).strip()
        if title:
            items.append({"title": title, "traffic": traffic, "news_snippet": news_title})

    return items


def pick_topic() -> dict:
    """Pick one trending topic to build a video around."""
    topics = get_trending_topics(limit=10)
    if not topics:
        raise RuntimeError("No trending topics returned - Google Trends feed may be unavailable.")
    return random.choice(topics[:5])


if __name__ == "__main__":
    topic = pick_topic()
    print(f"Picked trend: {topic['title']} (traffic: {topic['traffic']})")
