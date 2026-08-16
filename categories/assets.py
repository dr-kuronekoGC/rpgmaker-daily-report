# ==========================================
# Asset Classification
# ==========================================

from .keywords import (
    GRAPHIC_KEYWORDS,
    SOUND_KEYWORDS,
)


# ==========================================
# Strong keywords
# ==========================================

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
    "face set",
    "icon",
    "background",
    "texture",
    "pixel art",
    "pixel",
    "ui",
)


# ==========================================
# Asset size / pack keywords
# ==========================================

# 「大量の素材」「大規模セット」と比較的明確に
# 判断できるキーワードだけを対象にする。
#
# 1枚の画像に大量の素材が載っているだけの場合は、
# タイトルから判別できないことが多いため対象外。

LARGE_PACK_KEYWORDS = (
    "mega pack",
    "megapack",
    "mega-pack",
    "ultimate pack",
    "ultimate bundle",
    "complete pack",
    "complete bundle",
    "full pack",
    "full set",
    "massive pack",
    "large pack",
    "big pack",
    "huge pack",
    "asset pack",
    "asset bundle",
    "sprite pack",
    "sprite sheet pack",
    "tileset pack",
    "tileset collection",
    "icon pack",
    "icon set",
    "character pack",
    "character set",
    "faceset pack",
    "faceset set",
)


# ==========================================
# Fan work / derivative work
# ==========================================

FANWORK_KEYWORDS = (
    "fanart",
    "fan art",
    "fan-game",
    "fan game",
    "fangame",
    "crossover",
    "tribute",
    "pokemon",
    "mario",
    "zelda",
    "final fantasy",
    "dragon quest",
    "kingdom hearts",
    "disney",
    "marvel",
    "dc comics",
    "sonic",
    "kirby",
    "undertale",
    "fate",
    "genshin",
)


# ==========================================
# Official edit / RTP edit
# ==========================================

OFFICIAL_EDIT_KEYWORDS = (
    "rtp edit",
    "rtp edits",
    "official edit",
    "official edits",
    "rpg maker edit",
    "rpg maker edits",
    "mv rtp edit",
    "mz rtp edit",
    "vx ace rtp edit",
    "vx rtp edit",
)


# ==========================================
# Helpers
# ==========================================

def _contains_any(
    text,
    keywords,
):
    return any(
        keyword in text
        for keyword in keywords
    )


def _append_unique(
    tags,
    tag,
):
    if tag not in tags:
        tags.append(tag)


# ==========================================
# Asset Classification
# ==========================================

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

    タグ例
    -------
    tileset
    character
    icon
    faceset
    sprite
    bgm
    sfx
    large_pack
    fanwork
    official_edit
    """

    title = (
        title
        or ""
    ).lower().strip()

    url = (
        url
        or ""
    ).lower().strip()

    tags = []

    # ==================================
    # 共通属性
    # ==================================

    # 大量セット
    #
    # 「1枚の画像に大量の素材がある」
    # ケースはここでは判定しない。
    if _contains_any(
        title,
        LARGE_PACK_KEYWORDS,
    ):
        _append_unique(
            tags,
            "large_pack",
        )

    # 版権・二次創作らしいもの
    if _contains_any(
        title,
        FANWORK_KEYWORDS,
    ):
        _append_unique(
            tags,
            "fanwork",
        )

    # 公式素材の改変・アレンジらしいもの
    if _contains_any(
        title,
        OFFICIAL_EDIT_KEYWORDS,
    ):
        _append_unique(
            tags,
            "official_edit",
        )

    # ==================================
    # サウンド素材
    # ==================================

    if _contains_any(
        title,
        STRONG_SOUND_KEYWORDS,
    ):

        if (
            "bgm" in title
            or "music" in title
            or "soundtrack" in title
        ):
            _append_unique(
                tags,
                "bgm",
            )

        if (
            "sfx" in title
            or "sound effect" in title
            or "sound effects" in title
        ):
            _append_unique(
                tags,
                "sfx",
            )

        return (
            "サウンド素材",
            tags,
        )

    # ==================================
    # グラフィック素材
    # ==================================

    if _contains_any(
        title,
        STRONG_GRAPHIC_KEYWORDS,
    ):

        if "ui" in title:
            _append_unique(
                tags,
                "ui",
            )

        if "sprite" in title:
            _append_unique(
                tags,
                "sprite",
            )

        if "background" in title:
            _append_unique(
                tags,
                "background",
            )

        if (
            "tileset" in title
            or "tile" in title
        ):
            _append_unique(
                tags,
                "tileset",
            )

        if (
            "character" in title
            or "portrait" in title
            or "faceset" in title
            or "face set" in title
        ):
            _append_unique(
                tags,
                "character",
            )

        if "faceset" in title or "face set" in title:
            _append_unique(
                tags,
                "faceset",
            )

        if "icon" in title:
            _append_unique(
                tags,
                "icon",
            )

        return (
            "グラフィック素材",
            tags,
        )

    # ==================================
    # 従来のキーワード判定
    # ==================================

    if _contains_any(
        title,
        SOUND_KEYWORDS,
    ):
        return (
            "サウンド素材",
            tags,
        )

    if _contains_any(
        title,
        GRAPHIC_KEYWORDS,
    ):
        return (
            "グラフィック素材",
            tags,
        )

    return (
        None,
        tags,
    )