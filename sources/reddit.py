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


CATEGORY_KEYWORDS = {
    "RPGツクール製ゲーム": [
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
    ],

    "プラグイン": [
        "plugin",
        "script",
        "system plugin",
        "plugin finder",
    ],

    "グラフィック": [
        "tileset",
        "sprite",
        "asset pack",
        "character generator",
        "animation asset",
        "portrait",
        "battler",
        "faceset",
        "character sheet",
    ],

    "サウンド": [
        "bgm",
        "music pack",
        "sound pack",
        "audio asset",
        "music",
        "sound effect",
        "sfx",
        "ambient",
    ],

    "Tips": [
        "tutorial",
        "guide",
        "tips",
        "workflow",
        "how i made",
        "devlog",
    ],
}


def classify(title):

    title_lower = title.lower()

    for word in IGNORE_WORDS:
        if word in title_lower:
            return None

    for word in QUESTION_WORDS:
        if word in title_lower:
            return None

    extra_questions = [
        "thoughts?",
        "any suggestions",
        "recommendation",
        "recommendations",
    ]

    for word in extra_questions:
        if word in title_lower:
            return None

    for category, keywords in CATEGORY_KEYWORDS.items():

        for keyword in keywords:

            if keyword in title_lower:
                return category

    return None


def get_items(seen):

    feed = feedparser.parse(RSS_URL)

    print(f"[Reddit] RSS: {len(feed.entries)}件")

    adopted_items = []

    new_seen = seen.copy()

    for entry in feed.entries:

        url = entry.link

        if url in seen:
            continue

        new_seen.append(url)

        category = classify(entry.title)

        if category is None:
            continue

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

    print(
        f"[Reddit] New: {len(adopted_items)}"
    )

    return adopted_items, new_seen
