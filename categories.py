# ==========================================
# 表示カテゴリ
# ==========================================

DISPLAY_CATEGORY = {

    # ---------- 公式 ----------
    "本体ニュース": "本体ニュース",
    "UNITE": "UNITE",
    "Forum重要事項": "Forum重要事項",

    # ---------- Plugin ----------
    "Forumプラグイン": "プラグイン",
    "Redditプラグイン": "プラグイン",
    "Steamプラグイン": "プラグイン",

    # ---------- Material ----------
    "Forum素材": "素材",
    "Reddit素材": "素材",
    "Steam素材": "素材",

    # ---------- Game ----------
    "Forum作品": "ゲーム",
    "Redditゲーム": "ゲーム",
    "Steamゲーム": "ゲーム",

    # ---------- Tips ----------
    "RedditTips": "Tips",

    # ---------- Question ----------
    "Forum質問": "質問",
    "Reddit質問": "質問",
}


# ==========================================
# Reddit
# ==========================================

IGNORE_WORDS = (
    "screenshot saturday",
    "megathread",
    "weekly thread",
)

REDDIT_CATEGORY_KEYWORDS = {

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

    "Redditプラグイン": (
        "plugin",
        "plugins",
        "script",
        "engine",
        "system plugin",
        "plugin finder",
    ),

    "Reddit素材": (
        "tileset",
        "sprite",
        "asset",
        "portrait",
        "faceset",
        "battler",
        "character generator",
        "pixel art",
        "icon",
        "icons",
        "music pack",
        "bgm",
        "sound",
        "sfx",
    ),

    "RedditTips": (
        "tutorial",
        "guide",
        "tips",
        "workflow",
        "devlog",
        "making of",
        "process",
        "showcase",
    ),

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


# ==========================================
# Forum
# ==========================================

FORUM_IMPORTANT_KEYWORDS = (
    "forum",
    "closure",
    "migration",
    "archive",
    "faq",
    "announcement",
    "shutdown",
)

FORUM_IGNORE_KEYWORDS = (
    "farewell",
    "favorite",
    "what's your",
    "what is your",
    "real quick",
    "food",
    "color",
    "count",
    "forum game",
    "random",
    "off topic",
    "the end",
    "best friend",
    "memories",
)


# ==========================================
# Reddit
# ==========================================

def classify_reddit(title):

    title = title.lower()

    if any(word in title for word in IGNORE_WORDS):
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

    if any(word in title for word in FORUM_IMPORTANT_KEYWORDS):
        return "Forum重要事項"

    if any(word in title for word in FORUM_IGNORE_KEYWORDS):
        return None

    question_keywords = (
        "help",
        "looking for",
        "need",
        "question",
        "replace",
        "how",
        "how do",
        "how can",
        "can i",
        "can someone",
        "where can",
        "is there",
        "anyone know",
    )

    plugin_keywords = (
        "plugin",
        "engine",
        "script",
        "tool",
        "visustella",
        "mana",
        "aftermath",
        "battle",
    )

    resource_keywords = (
        "art",
        "resource",
        "tileset",
        "sprite",
        "character",
        "asset",
    )

    game_keywords = (
        "demo",
        "release",
        "released",
        "project",
        "chapter",
        "episode",
        "version",
        "beta",
        "alpha",
        "trailer",
    )

    if any(word in title for word in question_keywords):
        return "Forum質問"

    if any(word in title for word in plugin_keywords):
        return "Forumプラグイン"

    if any(word in title for word in resource_keywords):
        return "Forum素材"

    if any(word in title for word in game_keywords):
        return "Forum作品"

    return "Forum作品"


# ==========================================
# Steam
# ==========================================

def classify_steam(title):

    title = title.lower()

    if "unite" in title:
        return "UNITE"

    plugin_keywords = (
        "plugin",
        "engine",
        "tool",
    )

    material_keywords = (
        "asset",
        "tileset",
        "music",
        "bgm",
        "sprite",
        "character",
        "dlc",
        "pack",
    )

    game_keywords = (
        "game",
        "project",
    )

    if any(word in title for word in plugin_keywords):
        return "Steamプラグイン"

    if any(word in title for word in material_keywords):
        return "Steam素材"

    if any(word in title for word in game_keywords):
        return "Steamゲーム"

    return "本体ニュース"
