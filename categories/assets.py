import re
# ==========================================
# Asset 共通分類
# ==========================================
GRAPHIC_KEYWORDS = {
    "tileset": (
        "tileset",
        "tiles",
        "tile",
    ),
    "sprite": (
        "sprite",
        "character",
        "npc",
        "enemy",
        "monster",
        "battler",
    ),
    "portrait": (
        "portrait",
        "face",
        "faceset",
    ),
    "icon": (
        "icon",
        "icons",
    ),
    "ui": (
        "ui",
        "gui",
        "hud",
        "menu",
    ),
    "background": (
        "background",
        "parallax",
        "battleback",
        "environment",
        "map",
    ),
    "animation": (
        "animation",
        "effect",
        "effects",
    ),
    "graphic": (
        "pixel",
        "graphic",
        "asset",
        "assets",
        "prop",
        "props",
        "weapon",
        "armor",
        "building",
    ),
}
SOUND_KEYWORDS = {
    "bgm": (
        "bgm",
        "music",
        "music pack",
        "soundtrack",
        "ost",
    ),
    "sfx": (
        "sfx",
        "sound",
        "sound effect",
        "audio",
        "ambient",
        "voice",
        "wav",
        "ogg",
        "mp3",
        "loop",
    ),
}
PLUGIN_KEYWORDS = (
    "plugin",
    "plugins",
    "script",
    "tool",
    "editor",
    "engine",
    "generator",
    # RPG Maker系で頻出
    "battle",
    "quest",
    "inventory",
    "message",
    "hud",
    "craft",
    "skill tree",
    "save",
)
GAME_KEYWORDS = (
    "release",
    "released",
    "launch",
    "launched",
    "available now",
    "demo",
    "chapter",
    "episode",
)
PLUGIN_URL_WORDS = (
    "plugin",
    "plugins",
)
GRAPHIC_URL_WORDS = (
    "asset",
    "assets",
    "sprite",
    "tileset",
)
SOUND_URL_WORDS = (
    "music",
    "audio",
    "sound",
)
# ==========================================
# キーワード一致
# ==========================================
def contains_keyword(text, keyword):
    text = text.lower()
    keyword = keyword.lower()
    # 複数語キーワード
    if " " in keyword:
        return keyword in text
    # 単語単位で一致
    pattern = rf"\b{re.escape(keyword)}\b"
    return re.search(
        pattern,
        text,
    ) is not None
# ==========================================
# 共通分類
# ==========================================
def classify_asset(title, href=""):
    title = title.lower()
    href = href.lower()
    tags = []
    # ---------------------------------
    # URL優先判定
    # ---------------------------------
    if any(
        word in href
        for word in PLUGIN_URL_WORDS
    ):
        return "プラグイン", tags
    if any(
        word in href
        for word in SOUND_URL_WORDS
    ):
        return "サウンド素材", tags
    if any(
        word in href
        for word in GRAPHIC_URL_WORDS
    ):
        return "グラフィック素材", tags
    # ---------------------------------
    # Plugin
    # ---------------------------------
    if any(
        contains_keyword(
            title,
            word,
        )
        for word in PLUGIN_KEYWORDS
    ):
        return "プラグイン", tags
    # ---------------------------------
    # Sound
    # ---------------------------------
    for tag, words in SOUND_KEYWORDS.items():
        if any(
            contains_keyword(
                title,
                word,
            )
            for word in words
        ):
            tags.append(tag)
    if tags:
        return "サウンド素材", tags
    # ---------------------------------
    # Graphic
    # ---------------------------------
    for tag, words in GRAPHIC_KEYWORDS.items():
        if any(
            contains_keyword(
                title,
                word,
            )
            for word in words
        ):
            tags.append(tag)
    if tags:
        return "グラフィック素材", tags
    # ---------------------------------
    # Game
    # ---------------------------------
    if any(
        contains_keyword(
            title,
            word,
        )
        for word in GAME_KEYWORDS
    ):
        return "ゲーム公開", tags
    return None, []