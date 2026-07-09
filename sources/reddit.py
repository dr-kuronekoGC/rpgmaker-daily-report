import feedparser

from config import RSS_URL

QUESTION_WORDS = [
    "help",
    "need help",
    "looking for",
    "question",
    "how to",
    "how do",
    "can i",
    "which",
    "what",
]

IGNORE_WORDS = [
    "screenshot saturday",
    "megathread",
    "weekly thread",
]


def classify(title):

    title_lower = title.lower()

    for word in IGNORE_WORDS:
        if word in title_lower:
            return None

    question_words = QUESTION_WORDS + [
        "thoughts?",
        "any suggestions",
        "recommendation",
        "recommendations",
    ]

    for word in question_words:
        if word in title_lower:
            return None

    game_keywords = [
        "released",
        "release",
        "steam page",
        "trailer",
        "demo",
        "now out",
        "available now",
        "launch",
        "launched",
        "steam store page",
    ]

    for keyword in game_keywords:
        if keyword in title_lower:
            return "RPGツクール製ゲーム"

    plugin_keywords = [
        "plugin",
        "script",
        "system plugin",
        "plugin finder",
    ]

    for keyword in plugin_keywords:
        if keyword in title_lower:
            return "プラグイン"

    graphic_keywords = [
        "tileset",
        "sprite",
        "asset pack",
        "character generator",
        "animation asset",
        "portrait",
        "battler",
        "faceset",
        "character sheet",
    ]

    for keyword in graphic_keywords:
        if keyword in title_lower:
            return "グラフィック"

    sound_keywords = [
        "bgm",
        "music pack",
        "sound pack",
        "audio asset",
        "music",
        "sound effect",
        "sfx",
        "ambient",
    ]

    for keyword in sound_keywords:
        if keyword in title_lower:
            return "サウンド"

    tips_keywords = [
        "tutorial",
        "guide",
        "tips",
        "workflow",
        "how i made",
        "devlog",
    ]

    for keyword in tips_keywords:
        if keyword in title_lower:
            return "Tips"

    return None


def get_reddit_items(seen):

    feed = feedparser.parse(RSS_URL)

    print("取得件数:", len(feed.entries))

    new_seen = seen.copy()

    adopted_items = []

    for entry in feed.entries:

        url = entry.link

        if url in seen:
            continue

        new_seen.append(url)

        category = classify(entry.title)

        if category:

            adopted_items.append(
                {
                    "title": entry.title,
                    "url": url,
                    "category": category,
                }
            )

            print(
                f"[Reddit][{category}] {entry.title}"
            )

    return adopted_items, new_seen
