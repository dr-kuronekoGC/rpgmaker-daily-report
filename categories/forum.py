# ==========================================
# Forum Classification
# ==========================================

from .keywords import (
    PLUGIN_KEYWORDS,
    GRAPHIC_KEYWORDS,
    SOUND_KEYWORDS,
    GAME_KEYWORDS,
    QUESTION_KEYWORDS,
)


FORUM_IMPORTANT_KEYWORDS = (
    "forum",
    "closure",
    "migration",
    "archive",
    "faq",
    "announcement",
    "shutdown",
)

FORUM_IGNORE_KEYWORDS = (
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

FORUM_PLUGIN_EXTRA_KEYWORDS = (
    "engine",
    "system",
    "visustella",
)

FORUM_MATERIAL_EXTRA_KEYWORDS = (
    "art",
)

FORUM_GAME_EXTRA_KEYWORDS = (
    "project",
)


def _contains(
    title,
    keywords,
):
    return any(
        word in title
        for word in keywords
    )


def classify_forum(
    title,
    forum_name="",
):
    title = title.lower().strip()
    forum_name = forum_name.lower().strip()

    # ----------------------------
    # 重要事項
    # ----------------------------

    if _contains(
        title,
        FORUM_IMPORTANT_KEYWORDS,
    ):
        return "Forum重要事項"

    # ----------------------------
    # 除外
    # ----------------------------

    if _contains(
        title,
        FORUM_IGNORE_KEYWORDS,
    ):
        return None

    # ----------------------------
    # Forum名
    # ----------------------------

    if "resources" in forum_name:
        return "Forum素材"

    if "support" in forum_name:
        return "Forum質問"

    if "useful development tools" in forum_name:
        return "Forumプラグイン"

    if (
        "games in development" in forum_name
        or "completed games" in forum_name
    ):
        return "Forum作品"

    # ----------------------------
    # 質問
    # ----------------------------

    if _contains(
        title,
        QUESTION_KEYWORDS,
    ):
        return "Forum質問"

    # ----------------------------
    # プラグイン
    # ----------------------------

    if _contains(
        title,
        PLUGIN_KEYWORDS
        + FORUM_PLUGIN_EXTRA_KEYWORDS,
    ):
        return "Forumプラグイン"

    # ----------------------------
    # サウンド素材
    # ----------------------------

    if _contains(
        title,
        SOUND_KEYWORDS,
    ):
        return "Forumサウンド素材"

    # ----------------------------
    # グラフィック素材
    # ----------------------------

    if _contains(
        title,
        GRAPHIC_KEYWORDS
        + FORUM_MATERIAL_EXTRA_KEYWORDS,
    ):
        return "Forumグラフィック素材"

    # ----------------------------
    # ゲーム
    # ----------------------------

    if _contains(
        title,
        GAME_KEYWORDS
        + FORUM_GAME_EXTRA_KEYWORDS,
    ):
        return "Forum作品"

    return None
