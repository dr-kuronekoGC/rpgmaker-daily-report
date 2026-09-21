# ==========================================
# Reddit Classification
# ==========================================

from .keywords import (
    SOUND_KEYWORDS,
    GRAPHIC_KEYWORDS,
    PLUGIN_KEYWORDS,
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
)

GAME_KEYWORDS = (
    "released",
    "release",
    "demo",
    "trailer",
    "beta",
    "alpha",
    "chapter",
    "episode",
)


def _contains(title, keywords):
    return any(
        keyword in title
        for keyword in keywords
    )


def classify_reddit(title, url=""):

    title = title.lower().strip()

    # --------------------------------
    # 重要事項
    # --------------------------------

    if _contains(
        title,
        IMPORTANT_KEYWORDS,
    ):
        return "Reddit重要事項"

    # --------------------------------
    # 質問・相談は収集対象外
    # --------------------------------
    # Daily Reportでは質問をSlack通知しない。
    # mark_unclassified_seen=Trueにより、既取得扱いにする。

    if _contains(
        title,
        QUESTION_KEYWORDS,
    ):
        return None

    if (
        "?" in title
        or title.startswith("do these")
        or title.startswith("does anyone")
        or title.startswith("can anyone")
        or title.startswith("can someone")
        or title.startswith("anyone else")
    ):
        return None
        
    # --------------------------------
    # プラグイン
    # --------------------------------

    if _contains(
        title,
        PLUGIN_KEYWORDS,
    ):
        return "Redditプラグイン"

    # --------------------------------
    # サウンド素材
    # --------------------------------

    if _contains(
        title,
        SOUND_KEYWORDS,
    ):
        return "Redditサウンド素材"

    # --------------------------------
    # ゲーム
    # --------------------------------

    if _contains(
        title,
        GAME_KEYWORDS,
    ):
        return "Redditゲーム"

    if (
        "my game" in title
        or "my new game" in title
        or "new game" in title
    ):
        return "Redditゲーム"

    # --------------------------------
    # グラフィック素材
    # --------------------------------

    if _contains(
        title,
        GRAPHIC_KEYWORDS,
    ):
        return "Redditグラフィック素材"

    # --------------------------------
    # Tips
    # --------------------------------

    if _contains(
        title,
        TIPS_KEYWORDS,
    ):
        return "RedditTips"

    return None
