# ==========================================
# Reddit
# ==========================================

IGNORE_WORDS = (
    "screenshot saturday",
    "megathread",
    "weekly thread",
)

REDDIT_CATEGORY_KEYWORDS = {

    # ------------------------
    # Question
    # ------------------------

    "Reddit質問": (

        "help",
        "need help",
        "looking for",
        "question",
        "how to",
        "how do",
        "how can",
        "can i",
        "can someone",
        "where can",
        "which",
        "what",
        "thoughts",
        "recommendation",
        "recommendations",
        "is there",
        "anyone know",

    ),

    # ------------------------
    # Plugin
    # ------------------------

    "Redditプラグイン": (

        "plugin",
        "plugins",
        "script",
        "engine",
        "system plugin",
        "tool",

    ),

    # ------------------------
    # Material
    # ------------------------

    "Reddit素材": (

        "tileset",
        "sprite",
        "asset",
        "portrait",
        "faceset",
        "battler",
        "pixel",
        "icon",
        "icons",
        "music",
        "bgm",
        "sound",
        "audio",
        "sfx",
        "character generator",

    ),

    # ------------------------
    # Tips
    # ------------------------

    "RedditTips": (

        "tutorial",
        "guide",
        "tips",
        "workflow",
        "devlog",
        "making of",
        "process",

    ),

    # ------------------------
    # Game
    # ------------------------

    "Redditゲーム": (

        "release",
        "released",
        "announcement",
        "launch",
        "launched",
        "coming soon",
        "wishlist",
        "demo",
        "trailer",
        "steam",
        "available now",

    ),

}


def classify_reddit(title):

    title = title.lower()

    if any(
        word in title
        for word in IGNORE_WORDS
    ):
        return None

    for category, keywords in REDDIT_CATEGORY_KEYWORDS.items():

        if any(
            keyword in title
            for keyword in keywords
        ):
            return category

    return None
