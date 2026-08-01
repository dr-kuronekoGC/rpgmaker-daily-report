# ==========================================
# Asset 共通分類
# ==========================================

GRAPHIC_KEYWORDS = (

    # タイル
    "tileset",
    "tile",

    # キャラ
    "sprite",
    "character",
    "faceset",
    "face",
    "portrait",
    "battler",
    "enemy",

    # UI
    "icon",
    "icons",
    "ui",
    "gui",

    # 背景
    "parallax",
    "background",
    "battleback",

    # エフェクト
    "animation",
    "effect",
    "effects",

    # その他
    "pixel",
    "asset",
    "assets",
    "graphic",
)

SOUND_KEYWORDS = (

    "music",
    "bgm",
    "ost",
    "sound",
    "audio",
    "sfx",
    "ambient",
    "voice",
)

PLUGIN_KEYWORDS = (

    "plugin",
    "plugins",
    "tool",
    "editor",
    "engine",
    "generator",
    "script",
)

GAME_KEYWORDS = (

    "game",
    "demo",
    "project",
    "release",
    "released",
    "launch",
    "chapter",
    "episode",
)


# ==========================================
# 共通分類
# ==========================================

def classify_asset(title):

    title = title.lower()

    # -------------------------
    # Plugin
    # -------------------------

    if any(k in title for k in PLUGIN_KEYWORDS):
        return "プラグイン"

    # -------------------------
    # Sound
    # -------------------------

    if any(k in title for k in SOUND_KEYWORDS):
        return "サウンド素材"

    # -------------------------
    # Graphic
    # -------------------------

    if any(k in title for k in GRAPHIC_KEYWORDS):
        return "グラフィック素材"

    # -------------------------
    # Game
    # -------------------------

    if any(k in title for k in GAME_KEYWORDS):
        return "ゲーム公開"

    return None
