# ==========================================
# Asset Classification
# ==========================================

from .keywords import (
    GRAPHIC_KEYWORDS,
    SOUND_KEYWORDS,
    PLUGIN_KEYWORDS,
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


# 「これがタイトルやタグにあれば、
# 素材そのものの可能性が高い」キーワード。
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
    "ui",
    "user interface",
)


# ==========================================
# Map / Parallax
# ==========================================
#
# map / mapping / parallax は、
# 「素材」ではなく「作品・作例」の場合が多い。
#
# そのため、これらだけでは
# グラフィック素材と判定しない。
#
# pack / asset / resource / download などと
# 組み合わさった場合のみ素材候補とする。
# ==========================================

MAP_KEYWORDS = (
    "map",
    "maps",
    "mapping",
    "mapmaking",
    "parallax",
    "parallax mapping",
    "parallaxmap",
)


MAP_CONTEXT_KEYWORDS = (
    "map pack",
    "map set",
    "map collection",
    "map bundle",
    "map resource",
    "map resources",
    "map asset",
    "map assets",
    "parallax pack",
    "parallax set",
    "parallax collection",
    "parallax bundle",
    "parallax resource",
    "parallax resources",
    "parallax asset",
    "parallax assets",
    "downloadable map",
    "downloadable maps",
    "downloadable parallax",
    "free map",
    "free maps",
    "free parallax",
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
# Keywords suggesting a showcase / example
# ==========================================
#
# これらは単独では「素材ではない」と断定しない。
# ただし map / parallax と組み合わさった場合、
# 作例である可能性を高く見る。
# ==========================================

SHOWCASE_KEYWORDS = (
    "screenshot",
    "showcase",
    "showcasing",
    "practice",
    "map practice",
    "level design",
    "leveldesign",
    "game design",
    "gamedesign",
    "gameplay",
    "in-game",
    "ingame",
    "work in progress",
    "wip",
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
    # プラグイン
    # ======================================

    plugin_search_text = (
        title
        + " "
        + " ".join(
            normalized_source_tags
        )
    )

    if _contains_any(
        plugin_search_text,
        PLUGIN_KEYWORDS,
    ):
        return (
            "プラグイン",
            tags,
        )
        
    # ======================================
    # サウンド素材
    # ======================================
    #
    # タイトルだけでサウンドとは判定しない。
    #
    # 「タイトルに音楽系キーワード」
    # ＋
    # 「タグにも音楽系キーワード」
    #
    # の両方を満たした場合のみサウンド素材とする。
    #
    # OST は単独判定せず、タグとの組み合わせで扱う。
    # ======================================

    SOUND_TITLE_KEYWORDS = (
        "bgm",
        "music",
        "soundtrack",
        "ost",
        "sfx",
        "sound effect",
        "sound effects",
    )

    SOUND_TAG_KEYWORDS = (
        "bgm",
        "music",
        "soundtrack",
        "ost",
        "sfx",
        "sound effect",
        "sound effects",
        "audio",
    )

    has_sound_title = _contains_any(
        title,
        SOUND_TITLE_KEYWORDS,
    )

    has_sound_tag = _contains_any(
        " ".join(
            normalized_source_tags
        ),
        SOUND_TAG_KEYWORDS,
    )

    if (
        has_sound_title
        and has_sound_tag
    ):
        if (
            "bgm" in title
            or "music" in title
            or "soundtrack" in title
            or "ost" in title
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

    # ======================================
    # 強いグラフィック素材判定
    # ======================================
    #
    # map / mapping / parallax はここに
    # 含めない。
    #
    # これらは後段で個別に判定する。
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

        return (
            "グラフィック素材",
            tags,
        )

    # ======================================
    # Map / Parallax
    # ======================================
    #
    # map / mapping / parallax 単独では
    # 素材扱いしない。
    #
    # pack / resource / asset / downloadable
    # などが組み合わさった場合だけ
    # グラフィック素材とする。
    # ======================================

    has_map_keyword = _contains_any(
        searchable_text,
        MAP_KEYWORDS,
    )

    has_map_context = _contains_any(
        searchable_text,
        MAP_CONTEXT_KEYWORDS,
    )

    if (
        has_map_keyword
        and has_map_context
    ):

        _append_unique(
            tags,
            "map",
        )

        if (
            "parallax"
            in searchable_text
        ):
            _append_unique(
                tags,
                "parallax",
            )

        return (
            "グラフィック素材",
            tags,
        )

    # ======================================
    # Pack / Bundle
    # ======================================
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
    # asset / resource / art は単独で
    # 素材扱いしない。
    #
    # ここではタイトル側のキーワードだけを
    # 利用する。
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
            "map",
            "maps",
            "mapping",
            "parallax",
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

    # ======================================
    # 最後の保護判定
    #
    # map / mapping / parallax があり、
    # showcase / practice / leveldesign 等も
    # 含む場合は、素材にはしない。
    #
    # 明示的な素材キーワードがない以上、
    # 無理に素材扱いしない。
    # ======================================

    if (
        has_map_keyword
        and _contains_any(
            searchable_text,
            SHOWCASE_KEYWORDS,
        )
    ):
        return (
            None,
            tags,
        )

    return (
        None,
        tags,
    )
