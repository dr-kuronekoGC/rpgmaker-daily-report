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

    # ==================================
    # 情報源タグ
    # ==================================

    normalized_source_tags = []

    if isinstance(
        source_tags,
        (list, tuple, set),
    ):

        for source_tag in source_tags:

            if not isinstance(
                source_tag,
                str,
            ):
                continue

            normalized_tag = (
                source_tag
                .lower()
                .strip()
            )

            if normalized_tag:
                normalized_source_tags.append(
                    normalized_tag
                )

    # タイトル＋情報源タグ
    # を素材判定用の文字列にする。
    searchable_text = (
        title
        + " "
        + " ".join(
            normalized_source_tags
        )
    )

    # ==================================
    # 共通属性
    # ==================================

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

    # ==================================
    # サウンド素材
    # ==================================

    if _contains_any(
        searchable_text,
        STRONG_SOUND_KEYWORDS,
    ):

        if (
            "bgm" in searchable_text
            or "music" in searchable_text
            or "soundtrack" in searchable_text
        ):
            _append_unique(
                tags,
                "bgm",
            )

        if (
            "sfx" in searchable_text
            or "sound effect" in searchable_text
            or "sound effects" in searchable_text
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
        searchable_text,
        STRONG_GRAPHIC_KEYWORDS,
    ):

        if "ui" in searchable_text:
            _append_unique(
                tags,
                "ui",
            )

        if "sprite" in searchable_text:
            _append_unique(
                tags,
                "sprite",
            )

        if "background" in searchable_text:
            _append_unique(
                tags,
                "background",
            )

        if (
            "tileset" in searchable_text
            or "tile" in searchable_text
        ):
            _append_unique(
                tags,
                "tileset",
            )

        if (
            "character" in searchable_text
            or "portrait" in searchable_text
            or "faceset" in searchable_text
            or "face set" in searchable_text
        ):
            _append_unique(
                tags,
                "character",
            )

        if (
            "faceset" in searchable_text
            or "face set" in searchable_text
        ):
            _append_unique(
                tags,
                "faceset",
            )

        if "icon" in searchable_text:
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