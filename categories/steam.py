# ==========================================
# Steam Classification
# ==========================================

from .keywords import (
    PLUGIN_KEYWORDS,
    GAME_KEYWORDS,
    QUESTION_KEYWORDS,
)


def _contains(
    title,
    keywords,
):
    return any(
        keyword in title
        for keyword in keywords
    )


def classify_steam(
    title,
    url="",
):
    """
    Steam情報を分類する。
    """

    title = title.lower().strip()

    # ----------------------------
    # プラグイン
    # ----------------------------

    if _contains(
        title,
        PLUGIN_KEYWORDS,
    ):
        return "Steamプラグイン"

    # ----------------------------
    # 質問
    # ----------------------------

    if _contains(
        title,
        QUESTION_KEYWORDS,
    ):
        return "Steam質問"

    # ----------------------------
    # ゲーム
    # ----------------------------

    if _contains(
        title,
        GAME_KEYWORDS,
    ):
        return "Steamゲーム"

    return None