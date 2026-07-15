# ==========================================
# Reddit
# ==========================================

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

REDDIT_CATEGORY_KEYWORDS = {

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


# ==========================================
# Forum
# ==========================================

FORUM_IMPORTANT_KEYWORDS = (
    "forum",
    "closure",
    "migration",
    "archive",
    "faq",
    "important",
    "announcement",
)

FORUM_IGNORE_KEYWORDS = (
    "favorite",
    "count",
    "music",
    "food",
    "what are you",
    "random thoughts",
    "off topic",
)

# ==========================================
# Reddit
# ==========================================

def classify_reddit(title):

    title = title.lower()

    if any(word in title for word in IGNORE_WORDS):
        return None

    if any(word in title for word in QUESTION_WORDS):
        return None

    for category, keywords in REDDIT_CATEGORY_KEYWORDS.items():

        if any(keyword in title for keyword in keywords):
            return category

    return None


# ==========================================
# Official
# ==========================================

def classify_official(title):

    title = title.lower()

    if "unite" in title:
        return "UNITE"

    return "本体ニュース"


# ==========================================
# Forum
# ==========================================

def classify_forum(title):

    title = title.lower()

    if any(
        keyword in title
        for keyword in FORUM_IMPORTANT_KEYWORDS
    ):
        return "Forum重要事項"

    if any(
        keyword in title
        for keyword in FORUM_IGNORE_KEYWORDS
    ):
        return None

    return "Forum"
