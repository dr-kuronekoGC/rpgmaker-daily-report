# ==========================================
# 表示カテゴリ
# ==========================================

DISPLAY_CATEGORY = {

    # ----------------
    # 公式
    # ----------------

    "本体ニュース": "本体ニュース",
    "UNITE": "UNITE",
    "Forum重要事項": "Forum重要事項",

    # ----------------
    # Plugin
    # ----------------

    "Forumプラグイン": "プラグイン",
    "Redditプラグイン": "プラグイン",

    # ----------------
    # Material
    # ----------------

    "Forum素材": "素材",
    "Reddit素材": "素材",

    # ----------------
    # Game
    # ----------------

    "Forum作品": "ゲーム",
    "Redditゲーム": "ゲーム",

    # ----------------
    # Steam
    # ----------------
    
    "Steamプラグイン": "プラグイン",
    "Steam素材": "素材",
    "Steamゲーム": "ゲーム",
    "SteamUNITE": "UNITE",

    # ----------------
    # Tips
    # ----------------

    "RedditTips": "Tips",

    # ----------------
    # Question
    # ----------------

    "Forum質問": "質問",

}

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

    # ------------------------
    # Forum重要事項
    # ------------------------

    important_keywords = (
        "forum",
        "closure",
        "migration",
        "archive",
        "faq",
        "announcement",
        "shutdown",
    )

    if any(word in title for word in important_keywords):
        return "Forum重要事項"

    # ------------------------
    # 雑談除外
    # ------------------------

    ignore_keywords = (
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

    if any(word in title for word in ignore_keywords):
        return None

    plugin_keywords = (
        "plugin",
        "engine",
        "script",
        "tool",
        "visustella",
        "mana",
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
        "odyssey",
        "pilgrim",
        "game",
        "project",
    )

    question_keywords = (
        "help",
        "looking for",
        "replace",
        "how",
        "question",
    )

    if any(word in title for word in plugin_keywords):
        return "Forumプラグイン"

    if any(word in title for word in resource_keywords):
        return "Forum素材"

    if any(word in title for word in game_keywords):
        return "Forum作品"

    if any(word in title for word in question_keywords):
        return "Forum質問"

    return "Forum作品"

# ==========================================
# Steam
# ==========================================

def classify_steam(title):

    title = title.lower()

    if "unite" in title:
        return "SteamUNITE"

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
