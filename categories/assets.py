# ==========================================
# Asset Classification
# ==========================================

from .asset_keywords import (
    GRAPHIC_KEYWORDS,
    SOUND_KEYWORDS,
    PLUGIN_KEYWORDS,
    STRONG_SOUND_KEYWORDS,
    STRONG_GRAPHIC_KEYWORDS,
    DEVIANTART_RESOURCE_KEYWORDS,
    MAP_KEYWORDS,
    MAP_CONTEXT_KEYWORDS,
    PACK_KEYWORDS,
    LARGE_PACK_KEYWORDS,
    FANWORK_KEYWORDS,
    OFFICIAL_EDIT_KEYWORDS,
    RPGMAKER_KEYWORDS,
    SHOWCASE_KEYWORDS,
    DEVIANTART_PROJECT_KEYWORDS,
    DEVIANTART_DISTRIBUTION_KEYWORDS,
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


def _contains_word(
    text,
    keywords,
):
    import re

    for keyword in keywords:
        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(keyword)
            + r"(?![a-z0-9])"
        )

        if re.search(
            pattern,
            text,
        ):
            return True

    return False

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
    is_downloadable=None,
    description="",
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
        + " "
        + (
            description
            or ""
        ).lower()
    )

    # --------------------------------------
    # タイトル・URL・タグだけの検索対象
    # --------------------------------------

    metadata_search_text = (
        title
        + " "
        + url
        + " "
        + " ".join(
            normalized_source_tags
        )
    )

    # --------------------------------------
    # 説明文だけの検索対象
    # --------------------------------------

    description_search_text = (
        description
        or ""
    ).lower()
    
    # ======================================
    # DeviantArt ダウンロード可否
    # ======================================

    if (
        is_downloadable is False
    ):
        return (
            None,
            tags,
        )
        
    if (
        is_downloadable is True
        and not _contains_any(
            metadata_search_text,
            DEVIANTART_RESOURCE_KEYWORDS,
        )
    ):
        return (
            None,
            tags,
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
    # DeviantArt: 明らかな作品紹介を除外
    # ======================================
    #
    # ただし、配布・利用可能であることを示す
    # 記述がある場合は除外しない。
    #
    # 「自作ゲーム用に作った素材を配布」
    # まで落とさないための処理。
    # ======================================

    if (
        is_downloadable is True
        and _contains_any(
            metadata_search_text,
            DEVIANTART_RESOURCE_KEYWORDS,
        )
        and _contains_any(
            description_search_text,
            DEVIANTART_PROJECT_KEYWORDS,
        )
        and not _contains_any(
            description_search_text,
            DEVIANTART_DISTRIBUTION_KEYWORDS,
        )
    ):
        return (
            None,
            tags,
        )
    
    # ======================================
    # 強いグラフィック素材を先に判定
    # ======================================
    #
    # music など曖昧なキーワードが含まれていても、
    # tileset / sprite / character / faceset など
    # 明らかなグラフィック素材であれば、
    # グラフィックを優先する。
    # ======================================

    if _contains_any(
        metadata_search_text,
        STRONG_GRAPHIC_KEYWORDS,
    ):

        if _contains_word(
            metadata_search_text,
            (
                "ui",
                "user interface",
            ),
        ):
            _append_unique(
                tags,
                "ui",
            )

        if (
            "sprite" in metadata_search_text
            or "sprites" in metadata_search_text
        ):
            _append_unique(
                tags,
                "sprite",
            )

        if (
            "background" in metadata_search_text
            or "backgrounds" in metadata_search_text
        ):
            _append_unique(
                tags,
                "background",
            )

        if (
            "tileset" in metadata_search_text
            or "tilesets" in metadata_search_text
            or "tile set" in metadata_search_text
            or "tilemap" in metadata_search_text
        ):
            _append_unique(
                tags,
                "tileset",
            )

        if (
            "character" in metadata_search_text
            or "characters" in metadata_search_text
            or "portrait" in metadata_search_text
            or "portraits" in metadata_search_text
            or "faceset" in metadata_search_text
            or "face set" in metadata_search_text
        ):
            _append_unique(
                tags,
                "character",
            )

        if (
            "faceset" in metadata_search_text
            or "face set" in metadata_search_text
        ):
            _append_unique(
                tags,
                "faceset",
            )

        if (
            "icon" in metadata_search_text
            or "icons" in metadata_search_text
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

    has_sound_title = _contains_word(
        title,
        SOUND_TITLE_KEYWORDS,
    )

    has_sound_tag = _contains_word(
        " ".join(
             normalized_source_tags
        ),
        SOUND_TAG_KEYWORDS,
    )

    # タグが取得できる場合：
    #   タイトル＋音楽系タグでサウンド判定
    #
    # タグがない場合：
    #   タイトルの明確な音楽系キーワードを根拠に判定
    #
    # ただし Music Box など、グラフィック素材になり得る
    # 明らかな例外は除外する。

    has_graphic_music_exception = _contains_word(
        title,
        (
            "music box",
            "musical note",
            "music note",
            "music notes",
        ),
    )

    has_sound_evidence = (
        has_sound_tag
        or _contains_word(
            title,
            (
                "sfx",
                "sound effect",
                "sound effects",
            ),
        )
        or source_tags is None
    )

    if (
        has_sound_title
        and has_sound_evidence
        and not has_graphic_music_exception
    ):
        if _contains_word(
            title,
            (
                "bgm",
                "music",
                "soundtrack",
                "ost",
            ),
        ):

            _append_unique(
                tags,
                "bgm",
            )

        if _contains_word(
            title,
            (
                "sfx",
                "sound effect",
                "sound effects",
            ),
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

    # --------------------------------------
    # DeviantArt: map / parallax の作品紹介除外
    # --------------------------------------
    #
    # map は有用な素材なのでキーワード自体は残す。
    # ただし「自作ゲームの町」「制作中のプロジェクト」
    # など、明らかな作品紹介の場合は除外する。
    # --------------------------------------

    if (
        is_downloadable is True
        and _contains_any(
            metadata_search_text,
            MAP_KEYWORDS,
        )
        and _contains_any(
            searchable_text,
            DEVIANTART_PROJECT_KEYWORDS,
        )
    ):
        return (
            None,
            tags,
        )
    
    if (
        has_map_keyword
        and (
            has_map_context
            or (
                is_downloadable is True
                and _contains_any(
                    searchable_text,
                    RPGMAKER_KEYWORDS,
                )
            )
        )
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
