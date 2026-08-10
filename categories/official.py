# ==========================================
# Official Classification
# ==========================================

IMPORTANT_KEYWORDS = (
    "announcement",
    "update",
    "news",
    "version",
    "upgrade",
    "patch",
    "release",
)

UNITE_KEYWORDS = (
    "unite",
    "rpg maker unite",
)


def _contains(title, keywords):
    return any(
        keyword in title
        for keyword in keywords
    )


def classify_official(
    title,
    url="",
):
    """
    RPG Maker公式情報を分類する。
    """

    title = title.lower().strip()

    # ----------------------------
    # UNITE
    # ----------------------------

    if _contains(
        title,
        UNITE_KEYWORDS,
    ):
        return "UNITE"

    # ----------------------------
    # 本体ニュース
    # ----------------------------

    if _contains(
        title,
        IMPORTANT_KEYWORDS,
    ):
        return "本体ニュース"

    return None