QUESTION_WORDS = (
    "help",
    "need help",
    "looking for",
    "question",
    "how to",
    "how do",
    "can i",
    "which",
    "what",
    "thoughts?",
    "any suggestions",
    "recommendation",
    "recommendations",
)

IGNORE_WORDS = (
    "screenshot saturday",
    "megathread",
    "weekly thread",
)


CATEGORY_KEYWORDS = {

    "RPGツクール製ゲーム": (
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
    ),

    "プラグイン": (
        "plugin",
        "script",
        "system plugin",
        "plugin finder",
    ),

    "グラフィック": (
        "tileset",
        "sprite",
        "asset pack",
        "character generator",
        "animation asset",
        "portrait",
        "battler",
        "faceset",
        "character sheet",
    ),

    "サウンド": (
        "bgm",
        "music pack",
        "sound pack",
        "audio asset",
        "music",
        "sound effect",
        "sfx",
        "ambient",
    ),

    "Tips": (
        "tutorial",
        "guide",
        "tips",
        "workflow",
        "how i made",
        "devlog",
    ),
}


OFFICIAL_KEYWORDS = {

    "UNITE": (
        "unite",
    ),

    "Forum重要事項": (
        "forum",
        "yanfly",
        "migration",
        "archive",
    ),
}


def classify_reddit(title):

    title = title.lower()

    if any(word in title for word in IGNORE_WORDS):
        return None

    if any(word in title for word in QUESTION_WORDS):
        return None

    for category, keywords in CATEGORY_KEYWORDS.items():

        if any(keyword in title for keyword in keywords):
            return category

    return None


def classify_official(title):

    title = title.lower()

    for category, keywords in OFFICIAL_KEYWORDS.items():

        if any(keyword in title for keyword in keywords):
            return category

    return "本体ニュース"
