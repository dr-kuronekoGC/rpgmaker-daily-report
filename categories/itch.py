# ==========================================
# itch.io Classification
# ==========================================

PLUGIN_KEYWORDS = (
    "plugin",
    "plugins",
    "script",
    "tool",
    "extension",
)

SOUND_KEYWORDS = (
    "music",
    "bgm",
    "sound",
    "sfx",
    "audio",
)

GRAPHIC_KEYWORDS = (
    "asset",
    "assets",
    "tileset",
    "sprite",
    "portrait",
    "faceset",
    "character",
    "pixel",
    "icon",
    "background",
    "ui",
    "graphic",
    "art",
)

GAME_KEYWORDS = (
    "game",
    "demo",
    "release",
    "chapter",
    "episode",
    "beta",
    "alpha",
    "trailer",
)


def _contains(title, keywords):
    return any(
        keyword in title
        for keyword in keywords
    )


def classify_itch(
    title,
    url="",
):
    """
    itch.io コンテンツを分類する。
    """

    title = title.lower().strip()

    # ----------------------------
    # プラグイン
    # ----------------------------

    if _contains(
        title,
        PLUGIN_KEYWORDS,
    ):
        return "itchプラグイン"

    # ----------------------------
    # サウンド素材
    # ----------------------------

    if _contains(
        title,
        SOUND_KEYWORDS,
    ):
        return "itchサウンド素材"

    # ----------------------------
    # グラフィック素材
    # ----------------------------

    if _contains(
        title,
        GRAPHIC_KEYWORDS,
    ):
        return "itchグラフィック素材"

    # ----------------------------
    # ゲーム
    # ----------------------------

    if _contains(
        title,
        GAME_KEYWORDS,
    ):
        return "itchゲーム"

    return None