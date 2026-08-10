# ==========================================
# Forum Classification
# ==========================================

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

QUESTION_KEYWORDS = (
    "help",
    "looking for",
    "need",
    "question",
    "replace",
    "how",
    "why",
    "error",
    "issue",
    "problem",
)

PLUGIN_KEYWORDS = (
    "plugin",
    "plugins",
    "script",
    "tool",
    "engine",
    "system",
    "visustella",
)

MATERIAL_KEYWORDS = (
    "tileset",
    "sprite",
    "portrait",
    "faceset",
    "character",
    "asset",
    "pixel",
    "icon",
    "music",
    "bgm",
    "sound",
    "resource",
    "art",
)

GAME_KEYWORDS = (
    "release",
    "released",
    "demo",
    "chapter",
    "episode",
    "beta",
    "alpha",
    "trailer",
    "steam",
    "project",
)


def _contains(title, keywords):
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
    # タイトル
    # ----------------------------

    if _contains(
        title,
        QUESTION_KEYWORDS,
    ):
        return "Forum質問"

    if _contains(
        title,
        PLUGIN_KEYWORDS,
    ):
        return "Forumプラグイン"

    if _contains(
        title,
        MATERIAL_KEYWORDS,
    ):
        return "Forum素材"

    if _contains(
        title,
        GAME_KEYWORDS,
    ):
        return "Forum作品"

    return None