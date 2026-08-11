# ==========================================
# Asset Classification
# ==========================================

from .keywords import (
    GRAPHIC_KEYWORDS,
    SOUND_KEYWORDS,
)


# 明確に素材を示すキーワード
STRONG_SOUND_KEYWORDS = (
    "music",
    "bgm",
    "sound",
    "sfx",
    "audio",
    "soundtrack",
)


STRONG_GRAPHIC_KEYWORDS = (
    "sprite",
    "tileset",
    "tile",
    "character",
    "portrait",
    "faceset",
    "icon",
    "background",
    "texture",
    "pixel art",
    "pixel",
    "ui",
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
    url = url.lower().strip()

    tags = []

    # ==================================
    # サウンド素材
    # ==================================

    if any(
        keyword in title
        for keyword in STRONG_SOUND_KEYWORDS
    ):

        if (
            "bgm" in title
            or "music" in title
            or "soundtrack" in title
        ):
            tags.append("bgm")

        if (
            "sfx" in title
            or "sound effect" in title
            or "sound effects" in title
        ):
            tags.append("sfx")

        return "サウンド素材", tags

    # ==================================
    # グラフィック素材
    # ==================================

    if any(
        keyword in title
        for keyword in STRONG_GRAPHIC_KEYWORDS
    ):

        if "ui" in title:
            tags.append("ui")

        if "sprite" in title:
            tags.append("sprite")

        if "background" in title:
            tags.append("background")

        if (
            "tileset" in title
            or "tile" in title
        ):
            tags.append("tileset")

        if (
            "character" in title
            or "portrait" in title
            or "faceset" in title
        ):
            tags.append("character")

        if (
            "icon" in title
        ):
            tags.append("icon")

        return "グラフィック素材", tags

    # ==================================
    # 従来のキーワード判定
    # ==================================

    if any(
        keyword in title
        for keyword in SOUND_KEYWORDS
    ):
        return "サウンド素材", tags

    if any(
        keyword in title
        for keyword in GRAPHIC_KEYWORDS
    ):
        return "グラフィック素材", tags

    return None, []
