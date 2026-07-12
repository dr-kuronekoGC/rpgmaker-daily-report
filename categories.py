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


def classify_reddit(title):

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

    for category, keywords in CATEGORY_KEYWORDS.items():

        if any(keyword in title_lower for keyword in keywords):
            return category

    return None


def classify_official(title):

    title_lower = title.lower()

    if "unite" in title_lower:
        return "UNITE"

    if any(
        word in title_lower
        for word in (
            "forum",
            "yanfly",
            "migration",
            "archive",
        )
    ):
        return "Forum重要事項"

    return "本体ニュース"
