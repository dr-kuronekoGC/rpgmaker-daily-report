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
    "can someone",
    "where can",
    "which",
    "what",
    "thoughts?",
    "any suggestions",
    "recommendation",
    "recommendations",
    "is there",
    "anyone know",
)

IGNORE_WORDS = (
    "screenshot saturday",
    "megathread",
    "weekly thread",
)

REDDIT_CATEGORY_KEYWORDS = {

    "Redditゲーム": (
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

    "Redditプラグイン": (
        "plugin",
        "script",
        "system plugin",
        "plugin finder",
    ),

    "Reddit素材": (
        "tileset",
        "sprite",
        "asset pack",
        "character generator",
        "animation asset",
        "portrait",
        "battler",
        "faceset",
        "character sheet",
        "bgm",
        "music pack",
        "sound pack",
        "audio asset",
        "music",
        "sound effect",
        "sfx",
        "ambient",
    ),

    "RedditTips": (
        "tutorial",
        "guide",
        "tips",
        "workflow",
        "how i made",
        "devlog",
    ),

}


def classify_reddit(title):

    title = title.lower()

    if any(word in title for word in IGNORE_WORDS):
        return None

    if any(word in title for word in QUESTION_WORDS):
        return "Reddit質問"

    for category, keywords in REDDIT_CATEGORY_KEYWORDS.items():

        if any(keyword in title for keyword in keywords):
            return category

    return None
