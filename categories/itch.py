# ==========================================
# itch.io Classification
# ==========================================

from .keywords import (
    SOUND_KEYWORDS,
    GRAPHIC_KEYWORDS,
    PLUGIN_KEYWORDS,
    GAME_KEYWORDS,
)


def _contains(
    title,
    keywords,
):
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