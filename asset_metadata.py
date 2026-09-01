# ==========================================
# Asset Metadata
# ==========================================

from categories.assets import classify_asset


# ==========================================
# Asset Type
# ==========================================

ASSET_TYPE_GRAPHIC = "graphic"
ASSET_TYPE_SOUND = "sound"
ASSET_TYPE_PLUGIN = "plugin"
ASSET_TYPE_GAME = "game"
ASSET_TYPE_OTHER = "other"


# ==========================================
# Engine
# ==========================================

ENGINE_MZ = "MZ"
ENGINE_MV = "MV"
ENGINE_MV_TRINITY = "MV Trinity"
ENGINE_VX_ACE = "VX Ace"
ENGINE_VX = "VX"
ENGINE_XP = "XP"
ENGINE_2003 = "2003"
ENGINE_2000 = "2000"
ENGINE_95 = "95"
ENGINE_U2U = "U2U"
ENGINE_UNITE = "UNITE"
ENGINE_OTHER_RPG_MAKER = "その他RPG Maker"
ENGINE_OTHER_TKool = "その他ツクール"
ENGINE_GENERIC = "汎用"
ENGINE_UNKNOWN = "不明"


# ==========================================
# License Status
# ==========================================

LICENSE_FREE = "free"
LICENSE_PERMISSION = "permission"
LICENSE_RESTRICTED = "restricted"
LICENSE_UNKNOWN = "unknown"


# ==========================================
# Price Status
# ==========================================

PRICE_FREE = "free"
PRICE_PAID = "paid"
PRICE_UNKNOWN = "unknown"


# ==========================================
# Copyright Status
# ==========================================

COPYRIGHT_ORIGINAL = "original"
COPYRIGHT_OFFICIAL = "official"
COPYRIGHT_FANWORK = "fanwork"
COPYRIGHT_POSSIBLE_FANWORK = "possible_fanwork"
COPYRIGHT_UNKNOWN = "unknown"


# ==========================================
# Confidence
# ==========================================

CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"
CONFIDENCE_UNKNOWN = "unknown"


# ==========================================
# Helpers
# ==========================================

def _normalize_text(value):
    if not isinstance(value, str):
        return ""

    return value.lower().strip()


def _contains_any(text, keywords):
    return any(
        keyword in text
        for keyword in keywords
    )


# ==========================================
# Engine Detection
# ==========================================

def detect_engine(
    item,
):
    """
    素材・作品が対象としている
    RPG Maker / ツクールシリーズを判定する。

    判定対象:
        title
        description
        source_tags
        url

    複数エンジンに対応する場合は
    複数の値を返す。

    明確な記載がない場合は
    無理に推測せず「不明」とする。
    """

    title = _normalize_text(
        item.get("title", "")
    )

    description = _normalize_text(
        item.get("description", "")
    )

    url = _normalize_text(
        item.get("url", "")
    )

    source_tags = item.get(
        "source_tags",
        [],
    )

    if not isinstance(
        source_tags,
        list,
    ):
        source_tags = []

    tags_text = " ".join(
        _normalize_text(tag)
        for tag in source_tags
        if isinstance(tag, str)
    )

    text = " ".join(
        (
            title,
            description,
            tags_text,
            url,
        )
    )

    engines = []

    # --------------------------------------
    # RPG Maker U2U
    # --------------------------------------

    if _contains_any(
        text,
        (
            "rpg maker u2u",
            "rpgmaker u2u",
            "rpg maker unite 2",
            "rpgmaker unite 2",
            "u2u",
        ),
    ):
        engines.append(
            ENGINE_U2U
        )

    # --------------------------------------
    # RPG Maker MZ
    # --------------------------------------

    if _contains_any(
        text,
        (
            "rpg maker mz",
            "rpgmaker mz",
            "rpgツクールmz",
            "rpgツクールmz用",
        ),
    ):
        engines.append(
            ENGINE_MZ
        )

    # --------------------------------------
    # RPG Maker MV
    # --------------------------------------

    if _contains_any(
        text,
        (
            "rpg maker mv",
            "rpgmaker mv",
            "rpgツクールmv",
            "rpgツクールmv用",
        ),
    ):
        engines.append(
            ENGINE_MV
        )

    # --------------------------------------
    # MV Trinity
    # --------------------------------------

    if _contains_any(
        text,
        (
            "mv trinity",
            "rpg maker mv trinity",
            "rpgツクールmv trinity",
        ),
    ):
        if ENGINE_MV not in engines:
            engines.append(
                ENGINE_MV
            )

        engines.append(
            ENGINE_MV_TRINITY
        )

    # --------------------------------------
    # RPG Maker VX Ace
    # --------------------------------------

    if _contains_any(
        text,
        (
            "rpg maker vx ace",
            "rpgmaker vx ace",
            "rpgツクールvx ace",
            "rpgツクールvxace",
            "vx ace",
            "vxace",
        ),
    ):
        engines.append(
            ENGINE_VX_ACE
        )

    # --------------------------------------
    # RPG Maker VX
    # --------------------------------------

    if (
        ENGINE_VX_ACE not in engines
        and _contains_any(
            text,
            (
                "rpg maker vx",
                "rpgmaker vx",
                "rpgツクールvx",
            ),
        )
    ):
        engines.append(
            ENGINE_VX
        )

    # --------------------------------------
    # RPG Maker XP
    # --------------------------------------

    if _contains_any(
        text,
        (
            "rpg maker xp",
            "rpgmaker xp",
            "rpgツクールxp",
        ),
    ):
        engines.append(
            ENGINE_XP
        )

    # --------------------------------------
    # RPG Maker 2003
    # --------------------------------------

    if _contains_any(
        text,
        (
            "rpg maker 2003",
            "rpgmaker 2003",
            "rpgツクール2003",
        ),
    ):
        engines.append(
            ENGINE_2003
        )

    # --------------------------------------
    # RPG Maker 2000
    # --------------------------------------

    if _contains_any(
        text,
        (
            "rpg maker 2000",
            "rpgmaker 2000",
            "rpgツクール2000",
        ),
    ):
        engines.append(
            ENGINE_2000
        )

    # --------------------------------------
    # RPG Maker 95
    # --------------------------------------

    if _contains_any(
        text,
        (
            "rpg maker 95",
            "rpgmaker 95",
            "rpgツクール95",
            "rpgツクール95用",
        ),
    ):
        engines.append(
            ENGINE_95
        )

    # --------------------------------------
    # RPG Maker UNITE
    # --------------------------------------

    if _contains_any(
        text,
        (
            "rpg maker unite",
            "rpgmaker unite",
            "rpgツクールunite",
            "rpgツクール unite",
            "unite",
        ),
    ):
        engines.append(
            ENGINE_UNITE
        )

    # --------------------------------------
    # その他ツクール
    # --------------------------------------

    other_tkool_keywords = (
        "action game maker",
        "アクションゲームツクール",
        "pixel game maker",
        "pixel game maker mv",
        "アクションゲームツクールmv",
        "音楽ツクール",
        "music maker",
    )

    if _contains_any(
        text,
        other_tkool_keywords,
    ):
        engines.append(
            ENGINE_OTHER_TKool
        )

    # --------------------------------------
    # 明示的な「RPG Maker」
    # --------------------------------------

    if (
        not engines
        and _contains_any(
            text,
            (
                "rpg maker",
                "rpgmaker",
                "rpgツクール",
            ),
        )
    ):
        engines.append(
            ENGINE_OTHER_RPG_MAKER
        )

    # --------------------------------------
    # 汎用素材
    #
    # 明らかにエンジンに依存しない
    # 素材だけを汎用とする。
    # --------------------------------------

    if not engines:

        generic_keywords = (
            "concept art",
            "illustration",
            "illustrations",
            "wallpaper",
            "icon pack",
            "generic icons",
            "general purpose",
            "汎用素材",
            "イラスト",
            "コンセプトアート",
        )

        if _contains_any(
            text,
            generic_keywords,
        ):
            engines.append(
                ENGINE_GENERIC
            )

    # --------------------------------------
    # 不明
    # --------------------------------------

    if not engines:
        engines.append(
            ENGINE_UNKNOWN
        )

    # --------------------------------------
    # 重複除去
    # --------------------------------------

    unique_engines = []

    for engine in engines:

        if engine not in unique_engines:
            unique_engines.append(
                engine
            )

    return unique_engines


# ==========================================
# Asset Type
# ==========================================

def detect_asset_type(
    category,
    title,
):

    title = _normalize_text(
        title
    )

    if category in (
        "グラフィック素材",
        "グラフィック",
    ):
        return ASSET_TYPE_GRAPHIC

    if category in (
        "サウンド素材",
        "サウンド",
    ):
        return ASSET_TYPE_SOUND

    if category in (
        "プラグイン",
        "plugin",
    ):
        return ASSET_TYPE_PLUGIN

    if category in (
        "ゲーム",
        "game",
    ):
        return ASSET_TYPE_GAME

    if _contains_any(
        title,
        (
            "tileset",
            "sprite",
            "icon",
            "faceset",
            "character",
            "pixel art",
        ),
    ):
        return ASSET_TYPE_GRAPHIC

    if _contains_any(
        title,
        (
            "bgm",
            "music",
            "sound effect",
            "sfx",
        ),
    ):
        return ASSET_TYPE_SOUND

    return ASSET_TYPE_OTHER


# ==========================================
# Copyright / Fanwork
# ==========================================

def detect_copyright_status(
    asset_tags,
    title,
):

    title = _normalize_text(
        title
    )

    if "fanwork" in asset_tags:
        return (
            COPYRIGHT_FANWORK,
            CONFIDENCE_MEDIUM,
        )

    possible_keywords = (
        "fanart",
        "fan art",
        "fan game",
        "fangame",
        "crossover",
        "tribute",
    )

    if _contains_any(
        title,
        possible_keywords,
    ):
        return (
            COPYRIGHT_POSSIBLE_FANWORK,
            CONFIDENCE_MEDIUM,
        )

    return (
        COPYRIGHT_UNKNOWN,
        CONFIDENCE_UNKNOWN,
    )


# ==========================================
# Price / License
# ==========================================

def detect_price_and_license(
    item,
):

    price_status = PRICE_UNKNOWN
    license_status = LICENSE_UNKNOWN

    if item.get("price_status") in (
        PRICE_FREE,
        PRICE_PAID,
    ):
        price_status = item[
            "price_status"
        ]

    if item.get("license_status") in (
        LICENSE_FREE,
        LICENSE_PERMISSION,
        LICENSE_RESTRICTED,
    ):
        license_status = item[
            "license_status"
        ]

    return (
        price_status,
        license_status,
    )


# ==========================================
# Source Metadata
# ==========================================

def preserve_source_metadata(
    item,
):

    source_tags = item.get(
        "source_tags"
    )

    if isinstance(
        source_tags,
        list,
    ):
        item["source_tags"] = [
            tag
            for tag in source_tags
            if isinstance(
                tag,
                str,
            )
        ]

    description = item.get(
        "description"
    )

    if not isinstance(
        description,
        str,
    ):
        item.pop(
            "description",
            None,
        )

    elif not description.strip():
        item.pop(
            "description",
            None,
        )

    else:
        item["description"] = (
            description.strip()
        )

    license_name = item.get(
        "license"
    )

    if isinstance(
        license_name,
        str,
    ):

        license_name = (
            license_name.strip()
        )

        if license_name:
            item["license"] = (
                license_name
            )
        else:
            item.pop(
                "license",
                None,
            )

    author = item.get(
        "author"
    )

    if isinstance(
        author,
        str,
    ):

        author = author.strip()

        if author:
            item["author"] = author
        else:
            item.pop(
                "author",
                None,
            )

    return item


# ==========================================
# Asset Metadata
# ==========================================

def build_asset_metadata(
    item,
):

    item = item.copy()

    item = preserve_source_metadata(
        item
    )

    title = item.get(
        "title",
        "",
    )

    url = item.get(
        "url",
        "",
    )

    category = item.get(
        "category",
        "",
    )

    source_tags = item.get(
        "source_tags",
        [],
    )

    detected_category, asset_tags = (
        classify_asset(
            title,
            url,
            source_tags=source_tags,
        )
    )

    if detected_category:
        category_for_type = (
            detected_category
        )
    else:
        category_for_type = category

    asset_type = detect_asset_type(
        category_for_type,
        title,
    )

    # --------------------------------------
    # Engine
    # --------------------------------------

    item["engine"] = detect_engine(
        item
    )

    # --------------------------------------
    # Copyright
    # --------------------------------------

    (
        copyright_status,
        copyright_confidence,
    ) = detect_copyright_status(
        asset_tags,
        title,
    )

    # --------------------------------------
    # Price / License
    # --------------------------------------

    (
        price_status,
        license_status,
    ) = detect_price_and_license(
        item,
    )

    # --------------------------------------
    # Confidence
    # --------------------------------------

    if (
        price_status == PRICE_UNKNOWN
        and license_status == LICENSE_UNKNOWN
        and copyright_status
        == COPYRIGHT_UNKNOWN
    ):
        confidence = CONFIDENCE_UNKNOWN

    else:
        confidence = CONFIDENCE_MEDIUM

    # --------------------------------------
    # Basic asset metadata
    # --------------------------------------

    item["asset_type"] = (
        asset_type
    )

    item["asset_tags"] = (
        asset_tags
    )

    # --------------------------------------
    # Price
    # --------------------------------------

    item["price_status"] = (
        price_status
    )

    item["is_free"] = (
        True
        if price_status == PRICE_FREE
        else False
        if price_status == PRICE_PAID
        else None
    )

    item["is_paid"] = (
        True
        if price_status == PRICE_PAID
        else False
        if price_status == PRICE_FREE
        else None
    )

    # --------------------------------------
    # License
    # --------------------------------------

    item["license_status"] = (
        license_status
    )

    # --------------------------------------
    # Copyright
    # --------------------------------------

    item["copyright_status"] = (
        copyright_status
    )

    item["is_fanwork"] = (
        copyright_status
        in (
            COPYRIGHT_FANWORK,
            COPYRIGHT_POSSIBLE_FANWORK,
        )
    )

    # --------------------------------------
    # Official edit
    # --------------------------------------

    item["is_official_edit"] = (
        "official_edit"
        in asset_tags
    )

    # --------------------------------------
    # Official source
    # --------------------------------------

    item["is_official"] = None

    # --------------------------------------
    # Large pack
    # --------------------------------------

    item["large_pack"] = (
        "large_pack"
        in asset_tags
    )

    # --------------------------------------
    # Confidence
    # --------------------------------------

    item["copyright_confidence"] = (
        copyright_confidence
    )

    item["metadata_confidence"] = (
        confidence
    )

    return item


# ==========================================
# Apply
# ==========================================

def enrich_items(
    items,
):

    enriched = []

    for item in items:

        try:

            enriched.append(
                build_asset_metadata(
                    item
                )
            )

        except Exception as e:

            print(
                "[Asset Metadata] "
                f"Error: {e}"
            )

            enriched.append(
                item
            )

    return enriched
