# ==========================================
# Asset Classification
# ==========================================

GRAPHIC_KEYWORDS = (
    "tileset",
    "sprite",
    "portrait",
    "faceset",
    "character",
    "asset",
    "pixel",
    "icon",
    "background",
    "ui",
    "graphic",
    "art",
)

SOUND_KEYWORDS = (
    "music",
    "bgm",
    "sound",
    "sfx",
    "audio",
)


def classify_asset(
    title,
    url="",
):
    """
    素材系コンテンツを分類する。

    Returns
    -------
    tuple[str | None, list[str]]
        (カテゴリ, タグ)
    """

    title = title.lower()

    tags = []

    # ----------------------------
    # サウンド
    # ----------------------------

    if any(
        keyword in title
        for keyword in SOUND_KEYWORDS
    ):

        if "bgm" in title or "music" in title:
            tags.append("bgm")

        if (
            "sfx" in title
            or "sound effect" in title
        ):
            tags.append("sfx")

        return "サウンド素材", tags

    # ----------------------------
    # グラフィック
    # ----------------------------

    if any(
        keyword in title
        for keyword in GRAPHIC_KEYWORDS
    ):

        if "ui" in title:
            tags.append("ui")

        if "sprite" in title:
            tags.append("sprite")

        if "background" in title:
            tags.append("background")

        return "グラフィック素材", tags

    return None, []