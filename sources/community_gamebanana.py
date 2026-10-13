"""Collect reusable RPG Maker resources listed on GameBanana's public RSS API."""

import requests
from bs4 import BeautifulSoup

from config import GAMEBANANA_RSS, GAMEBANANA_SEEN_FILE, REQUEST_TIMEOUT
from sources.base import HEADERS


SEEN_FILE = GAMEBANANA_SEEN_FILE
SOURCE_NAME = "GameBanana RPG Maker"

QUESTION_MARKERS = (
    "looking for", "request", "requests", "help", "question",
    "how do i", "how to", "can someone", "need help", "support",
)
SHOWCASE_MARKERS = (
    "my game", "game showcase", "gameplay", "trailer", "demo release",
    "full game", "project showcase", "let's play", "lets play",
)
PLUGIN_MARKERS = (
    "plugin", "plugins", "script", "scripts", "javascript", "tool",
    "tools", "utility", "utilities", "extension",
)
SOUND_MARKERS = (
    "music", "sound", "audio", "bgm", "bgs", "sfx", "se pack",
    "soundtrack", "voice pack",
)
GRAPHIC_MARKERS = (
    "sprite", "sprites", "tileset", "tilesets", "character",
    "characters", "faceset", "face set", "battler", "battlers",
    "icon pack", "icons", "pixel art", "background", "battleback",
    "animation", "animations", "portrait", "font", "texture", "ui pack",
)
TUTORIAL_MARKERS = ("tutorial", "guide", "how-to", "how to use")


def _normalize(value):
    return " ".join(str(value or "").lower().split())


def classify(title, tags=""):
    title_text = _normalize(title)
    combined = _normalize(f"{title_text} {tags}")

    if not title_text:
        return None
    if any(marker in title_text for marker in QUESTION_MARKERS):
        return None
    if any(marker in title_text for marker in SHOWCASE_MARKERS):
        return None

    if any(marker in combined for marker in PLUGIN_MARKERS):
        return "GameBananaプラグイン・ツール"
    if any(marker in combined for marker in SOUND_MARKERS):
        return "GameBananaサウンド素材"
    if any(marker in combined for marker in GRAPHIC_MARKERS):
        return "GameBananaグラフィック素材"
    if any(marker in combined for marker in TUTORIAL_MARKERS):
        return "GameBanana開発Tips"
    return None


def extract_feed_entries(xml_text):
    """Parse GameBanana's public RSS response, including its nonstandard <items> wrapper."""
    soup = BeautifulSoup(xml_text, "html.parser")
    entries = []

    for item in soup.find_all("item"):
        title_tag = item.find("title")
        link_tag = item.find("link")
        if title_tag is None or link_tag is None:
            continue

        title = title_tag.get_text(" ", strip=True)
        url = link_tag.get_text(" ", strip=True)
        if not title or not url:
            continue

        # Only submissions and tools can be reusable resources. Questions and
        # works-in-progress are deliberately excluded before classification.
        if not any(part in url for part in ("/mods/", "/tools/")):
            continue

        entries.append({"title": title, "link": url})

    return entries


def get_items(seen):
    if not isinstance(seen, list):
        seen = []

    try:
        response = requests.get(
            GAMEBANANA_RSS,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        entries = extract_feed_entries(response.content)
        if not entries:
            # An empty feed may be legitimate, so do not fail just because
            # no currently listed item matched the supported URL types.
            soup = BeautifulSoup(response.content, "html.parser")
            if soup.find("rss") is None:
                raise ValueError("Response did not contain an RSS document")
    except Exception as exc:
        print(f"[{SOURCE_NAME}] RSS error: {exc}")
        return [], seen

    new_seen = list(seen)
    seen_set = set(seen)
    adopted = []

    for entry in entries:
        url = entry["link"]
        title = entry["title"]
        if url in seen_set:
            continue

        seen_set.add(url)
        new_seen.append(url)

        category = classify(title)
        if category is None:
            continue

        adopted.append({
            "title": title,
            "url": url,
            "category": category,
            "source": SOURCE_NAME,
            "language": "en",
        })

    if not seen:
        print(f"[{SOURCE_NAME}] Baseline: {len(new_seen)} feed items")
        return [], new_seen

    print(f"[{SOURCE_NAME}] New resource posts: {len(adopted)}")
    return adopted, new_seen
