# ==========================================
# Asset Classification
# ==========================================

from .keywords import (
    GRAPHIC_KEYWORDS,
    SOUND_KEYWORDS,
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

    title = title.lower().strip()

    tags = []

    # ----------------------------
    # サウンド
    # ----------------------------

    if any(
        keyword in title
        for keyword in SOUND_KEYWORDS
    ):

        if (
            "bgm" in title
            or "music" in title
        ):
            tags.append("bgm")

        if (
            "sfx" in title
            or "sound effect" in title
            or "sound effects" in title
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

        if "tileset" in title:
            tags.append("tileset")

        if (
            "character" in title
            or "portrait" in title
            or "faceset" in title
        ):
            tags.append("character")

        return "グラフィック素材", tags

    return None, []
