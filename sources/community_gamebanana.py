"""Collect reusable RPG Maker resources listed on GameBanana's public RSS API."""

import xml.etree.ElementTree as ET

import requests

from config import GAMEBANANA_RSS_URLS, GAMEBANANA_SEEN_FILE, REQUEST_TIMEOUT
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
ALLOWED_ITEM_PATHS = ("/mods/", "/tools/", "/sounds/", "/textures/", "/sprites/", "/skins/", "/fonts/", "/tutorials/")


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
    """Parse GameBanana's public RSS response, including its <items> wrapper."""
    root = ET.fromstring(xml_text)
    root_name = root.tag.rsplit("}", 1)[-1].lower()
    if root_name != "rss":
        raise ValueError("Response did not contain an RSS document")

    entries = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        if not title or not url:
            continue

        # Only resource-capable item types are considered. Questions and
        # works-in-progress are deliberately excluded before classification.
        if not url.startswith("https://gamebanana.com/"):
            continue
        if not any(part in url for part in ALLOWED_ITEM_PATHS):
            continue

        entries.append({"title": title, "link": url})

    return entries


def get_items(seen):
    if not isinstance(seen, list):
        seen = []

    entries_by_url = {}
    successful_feeds = 0

    for feed_number, feed_url in enumerate(GAMEBANANA_RSS_URLS, start=1):
        try:
            response = requests.get(
                feed_url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            # An empty feed is valid; malformed or blocked responses are not.
            feed_entries = extract_feed_entries(response.content)
            successful_feeds += 1
            print(
                f"[{SOURCE_NAME}] RSS feed {feed_number}/"
                f"{len(GAMEBANANA_RSS_URLS)}: valid entries={len(feed_entries)}"
            )
            for entry in feed_entries:
                entries_by_url[entry["link"]] = entry
        except Exception as exc:
            print(f"[{SOURCE_NAME}] RSS feed {feed_number} error: {exc}")

    # Preserve state if every endpoint failed; do not mistake a blocked response
    # for an empty feed and advance the baseline.
    if successful_feeds == 0:
        print(f"[{SOURCE_NAME}] No successful RSS feeds; seen state preserved.")
        return [], seen

    entries = list(entries_by_url.values())
    new_seen = list(seen)
    seen_set = set(seen)
    adopted = []
    unclassified_new = 0
    already_seen = 0

    for entry in entries:
        url = entry["link"]
        title = entry["title"]
        if url in seen_set:
            already_seen += 1
            continue

        seen_set.add(url)
        new_seen.append(url)

        category = classify(title)
        if category is None:
            unclassified_new += 1
            continue

        adopted.append({
            "title": title,
            "url": url,
            "category": category,
            "source": SOURCE_NAME,
            "language": "en",
        })

    print(
        f"[{SOURCE_NAME}] Feed total={len(entries)} / "
        f"already seen={already_seen} / "
        f"new classified={len(adopted)} / "
        f"new unclassified={unclassified_new}"
    )

    if not seen:
        print(f"[{SOURCE_NAME}] Baseline: {len(new_seen)} feed items")
        return [], new_seen

    print(f"[{SOURCE_NAME}] New resource posts: {len(adopted)}")
    return adopted, new_seen
