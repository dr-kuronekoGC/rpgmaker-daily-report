# ==========================================
# Forum
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


def classify_forum(title, forum_name=""):

    title = title.lower()
    forum_name = forum_name.lower()

    if any(word in title for word in FORUM_IMPORTANT_KEYWORDS):
        return "Forum重要事項"

    if any(word in title for word in FORUM_IGNORE_KEYWORDS):
        return None

    # ------------------------
    # フォーラム名優先
    # ------------------------

    if "resources" in forum_name:
        return "Forum素材"

    if "support" in forum_name:
        return "Forum質問"

    if "games in development" in forum_name:
        return "Forum作品"

    if "completed games" in forum_name:
        return "Forum作品"

    if "useful development tools" in forum_name:
        return "Forumプラグイン"

    # ------------------------
    # タイトル判定
    # ------------------------

    question_keywords = (
        "help",
        "looking for",
        "need",
        "question",
        "replace",
        "how",
        "how do",
        "how can",
        "can i",
        "can someone",
        "where can",
        "is there",
        "anyone know",
        "why",
        "error",
        "issue",
        "problem",
    )

    plugin_keywords = (
        "plugin",
        "plugins",
        "engine",
        "script",
        "tool",
        "system",
        "visustella",
        "mana",
        "aftermath",
        "battle",
    )

    resource_keywords = (
        "art",
        "resource",
        "tileset",
        "sprite",
        "portrait",
        "faceset",
        "character",
        "asset",
        "battler",
        "music",
        "bgm",
        "sound",
        "icon",
    )

    game_keywords = (
        "demo",
        "release",
        "released",
        "launch",
        "chapter",
        "episode",
        "version",
        "beta",
        "alpha",
        "trailer",
        "steam",
        "wishlist",
        "project",
        "odyssey",
        "pilgrim",
    )

    if any(word in title for word in question_keywords):
        return "Forum質問"

    if any(word in title for word in plugin_keywords):
        return "Forumプラグイン"

    if any(word in title for word in resource_keywords):
        return "Forum素材"

    if any(word in title for word in game_keywords):
        return "Forum作品"

    return None
