"""
trend_finder.py

Pulls today's trending searches from Google Trends' free public RSS feed
(no API key required), filters them down to a Tech & AI niche, and picks
one as the seed topic for the video.

If nothing trending matches the niche today, falls back to a curated list
of evergreen Tech & AI angles so the pipeline always has something to run.
"""

import random
import requests
import xml.etree.ElementTree as ET

TRENDS_RSS_URL = "https://trends.google.com/trending/rss?geo=US"

# Keywords used to detect whether a trending search is Tech & AI relevant.
NICHE_KEYWORDS = [
    "ai", "artificial intelligence", "chatgpt", "gemini", "claude", "openai",
    "google", "apple", "iphone", "android", "microsoft", "meta", "app",
    "software", "startup", "tech", "robot", "robotics", "chip", "nvidia",
    "quantum", "coding", "programmer", "cybersecurity", "hack", "data breach",
    "crypto", "bitcoin", "vr", "ar", "smartphone", "gadget", "elon musk",
    "spacex", "tesla", "self-driving", "algorithm", "computer",
]

# Evergreen fallback topics used when nothing trending today matches the niche.
FALLBACK_TOPICS = [
    "The AI tool nobody's talking about yet",
    "How AI chips actually work",
    "The biggest AI news this month",
    "AI tools that save hours every week",
    "How to tell if an image is AI-generated",
    "The AI safety debate, explained simply",
    "What's next after ChatGPT and Gemini",
    "AI agents: what they actually are",
    "Tech habits of highly productive developers",
    "The most useful AI features people ignore",
]


def get_trending_topics(limit: int = 30) -> list[dict]:
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


def _matches_niche(topic: dict) -> bool:
    haystack = f"{topic['title']} {topic.get('news_snippet', '')}".lower()
    return any(kw in haystack for kw in NICHE_KEYWORDS)


def pick_topic() -> dict:
    """Pick one Tech & AI trending topic. Falls back to a curated evergreen
    topic if nothing trending today matches the niche."""
    all_topics = get_trending_topics(limit=30)
    niche_matches = [t for t in all_topics if _matches_niche(t)]

    if niche_matches:
        return random.choice(niche_matches)

    fallback_title = random.choice(FALLBACK_TOPICS)
    return {"title": fallback_title, "traffic": "", "news_snippet": ""}


if __name__ == "__main__":
    topic = pick_topic()
    print(f"Picked topic: {topic['title']}")
