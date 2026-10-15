# ==========================================
# Asset Metadata Field Detection
# ==========================================

from asset_metadata_engine import (
    _normalize_text,
    _contains_any,
)


# ==========================================
# Asset Type
# ==========================================

ASSET_TYPE_GRAPHIC = "graphic"
ASSET_TYPE_SOUND = "sound"
ASSET_TYPE_PLUGIN = "plugin"
ASSET_TYPE_GAME = "game"
ASSET_TYPE_OTHER = "other"


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


def detect_classification_status(confidence):
    """
    自動分類の信頼度から、確認が必要かを決める。

    high:
        自動分類をそのまま採用。
    medium / low / unknown:
        人間確認待ち。
    """
    if confidence == CONFIDENCE_HIGH:
        return "auto"

    return "needs_review"


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
