"""Collect resource-oriented posts from the RM Planet community forum."""

import feedparser

from config import RMPLANET_RSS, RMPLANET_SEEN_FILE

SEEN_FILE = RMPLANET_SEEN_FILE
SOURCE_NAME = "RM Planet"

GRAPHIC_KEYWORDS = (
    "asset", "assets", "resource", "resources", "sprite", "sprites",
    "tileset", "tilesets", "character", "characters", "battler",
    "battlers", "faceset", "icon pack", "pixel art", "background",
    "battleback", "animation",
)
SOUND_KEYWORDS = (
    "audio", "sound", "sounds", "music", "bgm", "bgs", "sfx",
    "sound effect", "sound effects",
)
PLUGIN_KEYWORDS = (
    "plugin", "plugins", "script", "scripts", "javascript", "js ",
)
QUESTION_KEYWORDS = (
    "help", "question", "looking for", "request", "requests",
    "how do i", "how to", "need help", "can someone",
)


def classify(title, tags=""):
    text = " ".join(f"{title} {tags}".lower().split())
    title_text = " ".join(str(title or "").lower().split())

    if not title_text or any(word in title_text for word in QUESTION_KEYWORDS):
        return None
    if any(word in text for word in PLUGIN_KEYWORDS):
        return "RM Planetプラグイン"
    if any(word in text for word in SOUND_KEYWORDS):
        return "RM Planetサウンド素材"
    if any(word in text for word in GRAPHIC_KEYWORDS):
        return "RM Planetグラフィック素材"
    return None


def get_items(seen):
    if not isinstance(seen, list):
        seen = []

    new_seen = list(seen)
    seen_set = set(seen)
    adopted = []

    try:
        feed = feedparser.parse(RMPLANET_RSS)
        if getattr(feed, "bozo", False) and not feed.entries:
            status = getattr(feed, "status", None)
            exception = getattr(feed, "bozo_exception", None)
            raise ValueError(
                f"RSS feed could not be parsed (HTTP status={status}, "
                f"parser error={exception})"
            )
    except Exception as exc:
        print(f"[{SOURCE_NAME}] RSS error: {exc}")
        return [], seen

    for entry in feed.entries:
        url = entry.get("link")
        title = str(entry.get("title", "")).strip()
        if not url or not title or url in seen_set:
            continue

        tags = []
        for tag in entry.get("tags", []):
            if isinstance(tag, dict) and tag.get("term"):
                tags.append(str(tag["term"]))
        category = classify(title, " ".join(tags))

        # Record all feed entries so irrelevant discussions are not rechecked
        # every day, while only emitting posts likely to contain reusable assets.
        new_seen.append(url)
        seen_set.add(url)

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
