"""Collect reusable RPG Maker resources listed on GameBanana's public RSS API."""

import feedparser
import requests

from config import GAMEBANANA_RSS, GAMEBANANA_SEEN_FILE
from config import REQUEST_TIMEOUT
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


def get_tags(entry):
    tags = []
    for tag in entry.get("tags", []):
        if isinstance(tag, dict) and tag.get("term"):
            tags.append(str(tag["term"]))
    for category in entry.get("categories", []):
        if isinstance(category, str):
            tags.append(category)
    return " ".join(tags)


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
        feed = feedparser.parse(response.content)
        if getattr(feed, "bozo", False) and not feed.entries:
            raise ValueError(
                f"RSS could not be parsed (parser error={feed.bozo_exception})"
            )
    except Exception as exc:
        print(f"[{SOURCE_NAME}] RSS error: {exc}")
        return [], seen

    new_seen = list(seen)
    seen_set = set(seen)
    adopted = []

    for entry in feed.entries:
        url = str(entry.get("link", "")).strip()
        title = str(entry.get("title", "")).strip()
        if not url or not title or url in seen_set:
            continue

        seen_set.add(url)
        new_seen.append(url)

        category = classify(title, get_tags(entry))
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
