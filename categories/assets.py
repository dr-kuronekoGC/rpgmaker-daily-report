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
    "ost",
)


STRONG_GRAPHIC_KEYWORDS = (
    "sprite",
    "sprites",
    "tileset",
    "tilesets",
    "tile set",
    "tilemap",
    "character",
    "characters",
    "portrait",
    "portraits",
    "faceset",
    "face set",
    "icon",
    "icons",
    "background",
    "backgrounds",
    "texture",
    "textures",
    "pixel art",
    "pixelart",
    "pixel-art",
    "pixel",
    "ui",
    "user interface",
    "parallax",
    "map",
    "maps",
)


# ==========================================
# Pack / bundle keywords
# ==========================================

PACK_KEYWORDS = (
    "asset pack",
    "asset bundle",
    "resource pack",
    "resource bundle",
    "graphics pack",
    "graphic pack",
    "sprite pack",
    "sprite bundle",
    "tileset pack",
    "tileset bundle",
    "tileset collection",
    "tileset set",
    "icon pack",
    "icon set",
    "character pack",
    "character set",
    "faceset pack",
    "faceset set",
    "background pack",
    "background set",
    "ui pack",
    "ui set",
)


# ==========================================
# Asset size / pack keywords
# ==========================================

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
# RPG Maker specific keywords
# ==========================================

RPGMAKER_KEYWORDS = (
    "rpg maker",
    "rpgmaker",
    "rpg-maker",
    "rpgmaker mv",
    "rpgmaker mz",
    "rpg maker mv",
    "rpg maker mz",
    "rpgmakermv",
    "rpgmakermz",
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


def _normalize_source_tags(
    source_tags,
):
    normalized = []

    if not isinstance(
        source_tags,
        (list, tuple, set),
    ):
        return normalized

    for source_tag in source_tags:

        if not isinstance(
            source_tag,
            str,
        ):
            continue

        tag = (
            source_tag
            .lower()
            .strip()
        )

        if tag:
            normalized.append(
                tag
            )

    return normalized


# ==========================================
# Asset Classification
# ==========================================

def classify_asset(
    title,
    url="",
    source_tags=None,
):
    """
    素材系コンテンツを分類する。

    title:
        作品タイトル

    url:
        作品URL

    source_tags:
        情報源から取得したタグ。
        DeviantArtではMetadata APIのタグを利用する。

    Returns
    -------
    tuple[str | None, list[str]]
        (カテゴリ, タグ)
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

    normalized_source_tags = (
        _normalize_source_tags(
            source_tags
        )
    )

    # --------------------------------------
    # 検索対象
    #
    # タイトル・URL・情報源タグを統合する。
    # --------------------------------------

    searchable_text = (
        title
        + " "
        + url
        + " "
        + " ".join(
            normalized_source_tags
        )
    )

    # ======================================
    # RPG Maker関連タグ
    # ======================================

    if _contains_any(
        searchable_text,
        RPGMAKER_KEYWORDS,
    ):
        _append_unique(
            tags,
            "rpgmaker",
        )

    # ======================================
    # 共通属性
    # ======================================

    if _contains_any(
        searchable_text,
        LARGE_PACK_KEYWORDS,
    ):
        _append_unique(
            tags,
            "large_pack",
        )

    if _contains_any(
        searchable_text,
        FANWORK_KEYWORDS,
    ):
        _append_unique(
            tags,
            "fanwork",
        )

    if _contains_any(
        searchable_text,
        OFFICIAL_EDIT_KEYWORDS,
    ):
        _append_unique(
            tags,
            "official_edit",
        )

    # ======================================
    # サウンド素材
    # ======================================

    if _contains_any(
        searchable_text,
        STRONG_SOUND_KEYWORDS,
    ):

        if (
            "bgm" in searchable_text
            or "music" in searchable_text
            or "soundtrack" in searchable_text
            or "ost" in searchable_text
        ):
            _append_unique(
                tags,
                "bgm",
            )

        if (
            "sfx" in searchable_text
            or "sound effect"
            in searchable_text
            or "sound effects"
            in searchable_text
        ):
            _append_unique(
                tags,
                "sfx",
            )

        return (
            "サウンド素材",
            tags,
        )

    # ======================================
    # 強いグラフィック素材判定
    # ======================================

    if _contains_any(
        searchable_text,
        STRONG_GRAPHIC_KEYWORDS,
    ):

        if (
            "ui" in searchable_text
            or "user interface"
            in searchable_text
        ):
            _append_unique(
                tags,
                "ui",
            )

        if (
            "sprite" in searchable_text
            or "sprites" in searchable_text
        ):
            _append_unique(
                tags,
                "sprite",
            )

        if (
            "background"
            in searchable_text
            or "backgrounds"
            in searchable_text
        ):
            _append_unique(
                tags,
                "background",
            )

        if (
            "tileset"
            in searchable_text
            or "tilesets"
            in searchable_text
            or "tile set"
            in searchable_text
            or "tilemap"
            in searchable_text
        ):
            _append_unique(
                tags,
                "tileset",
            )

        if (
            "character"
            in searchable_text
            or "characters"
            in searchable_text
            or "portrait"
            in searchable_text
            or "portraits"
            in searchable_text
            or "faceset"
            in searchable_text
            or "face set"
            in searchable_text
        ):
            _append_unique(
                tags,
                "character",
            )

        if (
            "faceset"
            in searchable_text
            or "face set"
            in searchable_text
        ):
            _append_unique(
                tags,
                "faceset",
            )

        if (
            "icon"
            in searchable_text
            or "icons"
            in searchable_text
        ):
            _append_unique(
                tags,
                "icon",
            )

        if (
            "parallax"
            in searchable_text
        ):
            _append_unique(
                tags,
                "parallax",
            )

        if (
            "map"
            in searchable_text
            or "maps"
            in searchable_text
        ):
            _append_unique(
                tags,
                "map",
            )

        return (
            "グラフィック素材",
            tags,
        )

    # ======================================
    # Pack / Bundle
    #
    # 「asset」単独では素材扱いしない。
    # pack / bundle と組み合わさった場合のみ
    # グラフィック素材とする。
    # ======================================

    if _contains_any(
        searchable_text,
        PACK_KEYWORDS,
    ):

        return (
            "グラフィック素材",
            tags,
        )

    # ======================================
    # 従来のキーワード判定
    #
    # ただし「asset」「resource」「art」
    # 単独による誤分類を避ける。
    # ======================================

    safe_graphic_keywords = tuple(
        keyword
        for keyword in GRAPHIC_KEYWORDS
        if keyword not in (
            "asset",
            "assets",
            "resource",
            "resources",
            "art",
        )
    )

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
        safe_graphic_keywords,
    ):
        return (
            "グラフィック素材",
            tags,
        )

    return (
        None,
        tags,
    )