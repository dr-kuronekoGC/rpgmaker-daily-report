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
    "OpenGameArtプラグイン": "プラグイン",
    "Kenneyプラグイン": "プラグイン",

    # ---------- Material ----------
    "Forum素材": "素材",
    "Reddit素材": "素材",
    "Steam素材": "素材",
    "itch素材": "素材",
    "OpenGameArt素材": "素材",
    "Kenney素材": "素材",

    # ---------- Game ----------
    "Forum作品": "ゲーム",
    "Redditゲーム": "ゲーム",
    "Steamゲーム": "ゲーム",
    "itchゲーム": "ゲーム",

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
# Steam
# ==========================================

def classify_steam(title):

    title = title.lower()

    if "unite" in title:
        return "SteamUNITE"

    # ------------------------
    # Plugin
    # ------------------------

    plugin_keywords = (
        "plugin",
        "plugins",
        "script",
        "system",
        "engine",
        "tool",
        "builder",
        "generator",
    )

    # ------------------------
    # Material
    # ------------------------

    material_keywords = (
        "asset",
        "assets",
        "tileset",
        "tilesets",
        "music",
        "bgm",
        "sound",
        "audio",
        "portrait",
        "character",
        "faceset",
        "sprite",
        "pixel",
        "battleback",
        "enemy",
        "monster",
        "pack",
        "dlc",
    )

    # ------------------------
    # Game
    # ------------------------

    game_keywords = (
        "game",
        "project",
        "release",
        "released",
        "launch",
        "demo",
    )

    if any(word in title for word in plugin_keywords):
        return "Steamプラグイン"

    if any(word in title for word in material_keywords):
        return "Steam素材"

    if any(word in title for word in game_keywords):
        return "Steamゲーム"

    return "本体ニュース"

# ==========================================
# itch.io
# ==========================================

def classify_itch(title):

    title = title.lower()

    plugin_keywords = (
        "plugin",
        "tool",
        "system",
        "engine",
    )

    music_keywords = (
        "music",
        "bgm",
        "ost",
        "sound",
        "sfx",
        "audio",
    )

    graphic_keywords = (
        "tileset",
        "sprite",
        "portrait",
        "character",
        "pixel",
        "icon",
        "gui",
        "ui",
        "animation",
        "parallax",
        "battleback",
    )

    material_keywords = (
        "tileset",
        "sprite",
        "pixel",
        "icons",
        "icon",
        "portrait",
        "character",
        "generator",
        "asset",
        "pack",
        "music",
        "bgm",
        "sfx",
        "sound",
        "ui",
        "gui",
        "animation",
        "effects",
        "battleback",
        "parallax",
    )

    game_keywords = (
        "game",
        "rpg",
        "demo",
    )

    if any(k in title for k in plugin_keywords):
        return "itchプラグイン"

    if any(k in title for k in music_keywords):
        return "itch素材"

    if any(k in title for k in graphic_keywords):
        return "itch素材"

    if any(k in title for k in material_keywords):
        return "itch素材"

    if any(k in title for k in game_keywords):
        return "itchゲーム"

    # デフォルトは素材寄り
    return "itch素材"

# ==========================================
# OpenGameArt
# ==========================================

def classify_opengameart(title):

    title = title.lower()

    material_keywords = (
        "tileset",
        "tile",
        "sprite",
        "character",
        "portrait",
        "face",
        "battler",
        "icon",
        "icons",
        "ui",
        "gui",
        "background",
        "parallax",
        "animation",
        "effect",
        "pixel",
        "asset",
        "pack",
        "music",
        "bgm",
        "sound",
        "sfx",
        "audio",
        "ambient",
        "rpg",
    )

    if any(word in title for word in material_keywords):
        return "OpenGameArt素材"

    return None

    return "OpenGameArt素材"

# ==========================================
# Kenney
# ==========================================

def classify_kenney(title):

    title = title.lower()

    plugin_keywords = (
        "tool",
        "editor",
    )

    material_keywords = (
        "asset",
        "pack",
        "tileset",
        "sprite",
        "pixel",
        "ui",
        "icon",
        "music",
        "audio",
        "sound",
        "character",
        "platformer",
        "rpg",
    )

    if any(word in title for word in plugin_keywords):
        return "Kenneyプラグイン"

    if any(word in title for word in material_keywords):
        return "Kenney素材"

    return None

