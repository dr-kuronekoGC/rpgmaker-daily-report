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

    category = None

    # 将来用
    # tileset
    # portrait
    # icon
    # bgm
    # se
    # ui
    tags = []

    # -------------------------
    # Plugin
    # -------------------------

    if any(k in title for k in PLUGIN_KEYWORDS):
        category = "プラグイン"

    # -------------------------
    # Sound
    # -------------------------

    elif any(k in title for k in SOUND_KEYWORDS):
        category = "サウンド素材"

    # -------------------------
    # Graphic
    # -------------------------

    elif any(k in title for k in GRAPHIC_KEYWORDS):
        category = "グラフィック素材"

    # -------------------------
    # Game
    # -------------------------

    elif any(k in title for k in GAME_KEYWORDS):
        category = "ゲーム公開"

    return category
