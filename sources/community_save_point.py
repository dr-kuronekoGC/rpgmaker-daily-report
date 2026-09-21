import feedparser

from config import (
    SAVE_POINT_RSS,
    SAVE_POINT_SEEN_FILE,
)

SEEN_FILE = SAVE_POINT_SEEN_FILE
SOURCE_NAME = "Save-Point"

PLUGIN_KEYWORDS = (
    "plugin",
    "plugins",
    "rpgmaker mv/mz",
    "rpg maker mv/mz",
    "script",
)

SOUND_KEYWORDS = (
    "audio",
    "sound",
    "bgm",
    "bgs",
    "se",
    "music",
)

GRAPHIC_KEYWORDS = (
    "resource",
    "resources",
    "2d resources",
    "tileset",
    "sprite",
    "graphic",
    "graphics",
    "pixel",
)

TIPS_KEYWORDS = (
    "tutorial",
    "tips",
    "tip",
    "guide",
    "how-to",
    "development",
)

QUESTION_KEYWORDS = (
    "request",
    "question",
    "help",
)


def normalize_text(value):
    if not isinstance(value, str):
        return ""
    return " ".join(value.lower().split())


def get_entry_forum_name(entry):
    tags = entry.get("tags", [])

    names = []

    for tag in tags:
        if isinstance(tag, dict):
            term = tag.get("term")
            if isinstance(term, str):
                names.append(term.strip())

    categories = entry.get("categories", [])

    for category in categories:
        if isinstance(category, str):
            names.append(category.strip())

    return " / ".join(
        name for name in names if name
    )


def classify(title, forum_name):
    title_text = normalize_text(title)
    forum_text = normalize_text(forum_name)

    if any(
        keyword in title_text
        for keyword in QUESTION_KEYWORDS
    ):
        return None

    if any(
        keyword in forum_text
        for keyword in PLUGIN_KEYWORDS
    ) or any(
        keyword in title_text
        for keyword in PLUGIN_KEYWORDS
    ):
        return "Save-Pointプラグイン"

    if any(
        keyword in forum_text
        for keyword in SOUND_KEYWORDS
    ) or any(
        keyword in title_text
        for keyword in SOUND_KEYWORDS
    ):
        return "Save-Pointサウンド素材"

    if any(
        keyword in forum_text
        for keyword in GRAPHIC_KEYWORDS
    ) or any(
        keyword in title_text
        for keyword in GRAPHIC_KEYWORDS
    ):
        return "Save-Pointグラフィック素材"

    if any(
        keyword in forum_text
        for keyword in TIPS_KEYWORDS
    ) or any(
        keyword in title_text
        for keyword in TIPS_KEYWORDS
    ):
        return "Save-PointTips"

    return None


def get_items(seen):
    try:
        feed = feedparser.parse(
            SAVE_POINT_RSS
        )

        new_seen = list(seen)
        seen_set = set(seen)
        adopted_items = []

        for entry in feed.entries:
            url = entry.get("link")
            title = entry.get("title", "").strip()

            if not url or not title:
                continue

            if url in seen_set:
                continue

            forum_name = get_entry_forum_name(entry)

            category = classify(
                title,
                forum_name,
            )

            new_seen.append(url)
            seen_set.add(url)

            if category is None:
                continue

            adopted_items.append(
                {
                    "title": title,
                    "url": url,
                    "category": category,
                    "source": SOURCE_NAME,
                }
            )

            print(
                f"[{SOURCE_NAME}]"
                f"[{category}] {title}"
            )

        if not seen:
            print(
                f"[{SOURCE_NAME}] Baseline: "
                f"{len(new_seen)} items"
            )
            return [], new_seen

        print(
            f"[{SOURCE_NAME}] New: "
            f"{len(adopted_items)}"
        )

        return adopted_items, new_seen

    except Exception as e:
        print(
            f"[{SOURCE_NAME}] Error: {e}"
        )
        return [], seen
