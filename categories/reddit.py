# ==========================================
# Reddit Classification
# ==========================================

IMPORTANT_KEYWORDS = (
    "official",
    "announcement",
    "update",
    "release",
)

PLUGIN_KEYWORDS = (
    "plugin",
    "plugins",
    "script",
    "visustella",
    "hakuen",
    "casper",
    "galv",
)

ASSET_KEYWORDS = (
    "asset",
    "assets",
    "resource",
    "resources",
    "tileset",
    "sprite",
    "portrait",
    "faceset",
    "character",
    "pixel",
    "icon",
    "music",
    "bgm",
    "sound",
    "sfx",
)

GAME_KEYWORDS = (
    "release",
    "released",
    "game",
    "demo",
    "chapter",
    "episode",
    "beta",
    "alpha",
    "trailer",
    "steam",
)

QUESTION_KEYWORDS = (
    "help",
    "question",
    "how",
    "why",
    "looking for",
    "need",
    "error",
    "issue",
    "problem",
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

    Returns
    -------
    str | None
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
    # 素材
    # ----------------------------

    if _contains(
        title,
        ASSET_KEYWORDS,
    ):

        if _contains(
            title,
            SOUND_KEYWORDS,
        ):
            return "Redditサウンド素材"

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


SOUND_KEYWORDS = (
    "music",
    "bgm",
    "sound",
    "sfx",
    "audio",
)