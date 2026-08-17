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

    # --------------------------------------
    # タイトルによる補助判定
    # --------------------------------------

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
    """
    版権・二次創作の可能性を判定する。

    注意:
    これは法的な著作権判定ではない。
    明らかなキーワードがある場合だけ
    fanwork / possible_fanwork とする。
    """

    title = _normalize_text(title)

    if "fanwork" in asset_tags:
        return (
            COPYRIGHT_FANWORK,
            CONFIDENCE_MEDIUM,
        )

    # assets.py の fanwork キーワードで
    # 拾えなかった場合に備えた追加候補
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
    """
    価格・ライセンス情報を判定する。

    現段階では、情報源から明示的な情報を
    取得できていないため、基本的に unknown。

    今後、DeviantArt APIなどから得られた
    明示的な情報をここに渡して判定する。
    """

    price_status = PRICE_UNKNOWN
    license_status = LICENSE_UNKNOWN

    # --------------------------------------
    # 明示的な値が既に入っている場合
    # --------------------------------------

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
# Asset Metadata
# ==========================================

def build_asset_metadata(item):
    """
    収集アイテムから素材評価用メタデータを作る。

    情報が確認できない場合は unknown とする。
    推測による「無料」「利用可能」判定は行わない。
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
    # Asset classification
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

    item["asset_type"] = asset_type

    item["asset_tags"] = asset_tags

    # --------------------------------------
    # Price
    # --------------------------------------

    item["price_status"] = price_status

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
        "official_edit" in asset_tags
    )

    # --------------------------------------
    # Official source
    # --------------------------------------

    # 現段階ではサイトごとの情報を
    # まだ解析していないため unknown。
    item["is_official"] = None

    # --------------------------------------
    # Large pack
    # --------------------------------------

    item["large_pack"] = (
        "large_pack" in asset_tags
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

            print(
                "[Asset Metadata] "
                f"Error: {e}"
            )

            # 分類失敗時にも元データを捨てない
            enriched.append(
                item
            )

    return enriched
