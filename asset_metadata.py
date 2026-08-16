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
# Asset Type
# ==========================================

def detect_asset_type(
    category,
    title,
):
    """
    内部カテゴリから素材種別を判定する。
    """

    title = _normalize_text(title)

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

    # 念のためタイトルからも補助判定
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
# Metadata
# ==========================================

def build_asset_metadata(item):
    """
    収集アイテムから素材評価用メタデータを作る。

    この段階では、
    価格・ライセンスについて推測しない。
    情報がなければ unknown とする。
    """

    item = item.copy()

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

    # --------------------------------------
    # assets.py の分類を利用
    # --------------------------------------

    detected_category, asset_tags = (
        classify_asset(
            title,
            url,
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
    # Fanwork
    # --------------------------------------

    is_fanwork = (
        "fanwork" in asset_tags
    )

    # --------------------------------------
    # Official edit
    # --------------------------------------

    is_official_edit = (
        "official_edit" in asset_tags
    )

    # --------------------------------------
    # Large pack
    # --------------------------------------

    large_pack = (
        "large_pack" in asset_tags
    )

    # --------------------------------------
    # Metadata
    # --------------------------------------

    item["asset_type"] = asset_type

    item["asset_tags"] = asset_tags

    item["is_free"] = None

    item["is_paid"] = None

    item["price_status"] = PRICE_UNKNOWN

    item["license_status"] = LICENSE_UNKNOWN

    item["is_official"] = None

    item["is_fanwork"] = is_fanwork

    item["is_official_edit"] = (
        is_official_edit
    )

    item["large_pack"] = large_pack

    return item


# ==========================================
# Apply
# ==========================================

def enrich_items(items):
    """
    複数アイテムに素材メタデータを付加する。
    """

    enriched = []

    for item in items:

        try:

            enriched.append(
                build_asset_metadata(
                    item
                )
            )

        except Exception as e:

            # 分類に失敗しても、
            # 元のアイテムを捨てない。
            print(
                "[Asset Metadata] "
                f"Error: {e}"
            )

            enriched.append(
                item
            )

    return enriched