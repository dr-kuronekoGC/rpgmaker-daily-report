# ==========================================
# Reddit Classification
# ==========================================

from .keywords import (
    SOUND_KEYWORDS,
    GRAPHIC_KEYWORDS,
    PLUGIN_KEYWORDS,
    GAME_KEYWORDS,
    QUESTION_KEYWORDS,
)


IMPORTANT_KEYWORDS = (
    "official",
    "announcement",
    "major update",
    "new version",
    "version update",
)

TIPS_KEYWORDS = (
    "tip",
    "tips",
    "tutorial",
    "guide",
    "how to",
)


def _contains(
    title,
    keywords,
):
    return any(
        keyword in title
        for keyword in keywords
    )


def classify_reddit(
    title,
    url="",
):
    """
    Reddit投稿を分類する。
    """

    title = title.lower().strip()

    # ----------------------------
    # 重要事項
    # ----------------------------

    if _contains(
        title,
        IMPORTANT_KEYWORDS,
    ):
        return "Reddit重要事項"

    # ----------------------------
    # プラグイン
    # ----------------------------

    if _contains(
        title,
        PLUGIN_KEYWORDS,
    ):
        return "Redditプラグイン"

    # ----------------------------
    # サウンド素材
    # ----------------------------

    if _contains(
        title,
        SOUND_KEYWORDS,
    ):
        return "Redditサウンド素材"

    # ----------------------------
    # グラフィック素材
    # ----------------------------

    if _contains(
        title,
        GRAPHIC_KEYWORDS,
    ):
        return "Redditグラフィック素材"

    # ----------------------------
    # ゲーム
    # ----------------------------

    if _contains(
        title,
        GAME_KEYWORDS,
    ):
        return "Redditゲーム"

    # ----------------------------
    # Tips
    # ----------------------------

    if _contains(
        title,
        TIPS_KEYWORDS,
    ):
        return "RedditTips"

    # ----------------------------
    # 質問
    # ----------------------------

    if _contains(
        title,
        QUESTION_KEYWORDS,
    ):
        return "Reddit質問"

    return None
