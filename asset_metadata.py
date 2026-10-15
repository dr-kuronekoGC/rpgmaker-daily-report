# ==========================================
# Asset Metadata
# ==========================================

import re

from categories.assets import classify_asset

from asset_metadata_fields import (
    ASSET_TYPE_GRAPHIC,
    ASSET_TYPE_SOUND,
    ASSET_TYPE_PLUGIN,
    ASSET_TYPE_GAME,
    ASSET_TYPE_OTHER,
    LICENSE_FREE,
    LICENSE_PERMISSION,
    LICENSE_RESTRICTED,
    LICENSE_UNKNOWN,
    PRICE_FREE,
    PRICE_PAID,
    PRICE_UNKNOWN,
    COPYRIGHT_ORIGINAL,
    COPYRIGHT_OFFICIAL,
    COPYRIGHT_FANWORK,
    COPYRIGHT_POSSIBLE_FANWORK,
    COPYRIGHT_UNKNOWN,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_LOW,
    CONFIDENCE_UNKNOWN,
    detect_classification_status,
    detect_asset_type,
    detect_copyright_status,
    detect_price_and_license,
    preserve_source_metadata,
)

from asset_metadata_intent import (
    _is_non_asset_category,
    _is_non_asset_title,
    _is_explicit_plugin_category,
    _is_explicit_game_category,
    classify_resource_intent,
)

from classification_scoring import (
    classify_sound_with_evidence,
    classify_taxonomy_with_evidence,
)

from asset_metadata_engine import (
    ENGINE_MZ,
    ENGINE_MV,
    ENGINE_MV_TRINITY,
    ENGINE_VX_ACE,
    ENGINE_VX,
    ENGINE_XP,
    ENGINE_2003,
    ENGINE_2000,
    ENGINE_95,
    ENGINE_U2U,
    ENGINE_UNITE,
    ENGINE_OTHER_RPG_MAKER,
    ENGINE_OTHER_TKool,
    ENGINE_GENERIC,
    ENGINE_UNKNOWN,
    _normalize_text,
    _contains_any,
    detect_engine,
)


# ==========================================
# Detailed taxonomy
# ==========================================

GRAPHIC_SUBCATEGORY_KEYWORDS = {
    "character": ("character", "characters", "charset", "character sheet", "character base"),
    "sv_character": ("sv character", "sv battler", "side-view character", "side view character"),
    "enemy_battler": ("enemy battler", "battler", "monster sprite"),
    "face": ("faceset", "face set", "face graphic", "face graphics"),
    "bust": ("bust", "bustup", "bust up"),
    "full_art": ("illustration", "full art", "key art", "concept art"),
    "tileset": ("tileset", "tile set", "tilemap", "tilesheet"),
    "battle_background": ("battleback", "battle background"),
    "parallax": ("parallax",),
    "animation": ("animation", "effect animation", "effekseer"),
    "icon": ("icon", "icons", "icon set", "icon pack"),
    "ui_system": ("ui", "user interface", "window skin", "windowskin"),
    "title": ("title screen", "title graphic", "title logo"),
}

PLUGIN_CATEGORY_KEYWORDS = {
    "system_core": ("core", "system", "engine", "utility"),
    "battle": ("battle", "combat", "action battle", "atb", "ctb"),
    "skills_states": ("skill", "skills", "state", "states", "buff", "debuff"),
    "menu_ui": ("menu", "hud", "ui", "window", "status menu"),
    "items_equipment": ("item", "items", "equipment", "equip"),
    "shop": ("shop", "merchant"),
    "character_party": ("party", "actor", "actors", "character", "formation"),
    "quest": ("quest", "journal", "mission"),
    "map_events": ("map", "event", "events", "movement"),
    "save_load": ("save", "load", "autosave"),
    "messages_dialogue": ("message", "messages", "dialogue", "dialog", "text"),
    "audio": ("audio", "sound", "bgm", "bgs", "me", "se"),
    "graphics": ("graphic", "graphics", "sprite", "picture", "animation"),
    "database": ("database", "db", "notetag"),
    "development_debug": ("debug", "developer", "development", "test", "console"),
    "network_external": ("network", "api", "http", "web", "discord", "integration", "external"),
}

def _contains_keyword(text, keywords):
    """
    キーワードを単純な部分一致ではなく、単語境界を考慮して判定する。
    特に ME / SE / UI / DB / API のような短い語が、
    game / use / build など別の単語に誤反応するのを防ぐ。
    """
    import re

    normalized = str(text or "").lower()
    for keyword in keywords:
        k = str(keyword or "").strip().lower()
        if not k:
            continue
        pattern = r"(?<![a-z0-9])" + re.escape(k) + r"(?![a-z0-9])"
        if re.search(pattern, normalized):
            return True
    return False

def detect_detailed_subcategory(
    item,
    asset_type,
    asset_tags,
    classification_result=None,
):
    """
    Evidence-based detailed taxonomy.

    The source-native metadata is preserved and weighted more heavily
    than free-form description text. Multiple strong categories are allowed
    when an item genuinely belongs to more than one subcategory.

    A precomputed classification_result can be supplied by the metadata
    builder so the same taxonomy does not need to be scored repeatedly.
    """

    if asset_type == ASSET_TYPE_GRAPHIC:
        result = classification_result
        if result is None:
            result = classify_taxonomy_with_evidence(item, "graphic")
        return result["categories"]

    if asset_type == ASSET_TYPE_PLUGIN:
        result = classification_result
        if result is None:
            result = classify_taxonomy_with_evidence(item, "plugin")
        return result["categories"]

    if asset_type == ASSET_TYPE_SOUND:
        result = classification_result
        if result is None:
            result = classify_sound_with_evidence(item)
        return [
            result["sound_type"].lower()
            if result["sound_type"]
            else "other"
        ]

    return []

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

    detected_category = None
    asset_tags = []

    # 質問・相談・ニュース等は、タイトル中の
    # "music" や "sound" だけで素材化しない。
    body_parts = [
        item.get(field, "")
        for field in ("description", "body_text", "post_body", "body", "content_text", "content", "text")
        if isinstance(item.get(field), str) and item.get(field, "").strip()
    ]
    description_for_classification = " ".join(body_parts)

    preliminary_intent, _, _ = classify_resource_intent(item)

    # A clear question/showcase is not promoted by generic asset keywords.
    # If the body explicitly contains distribution/release evidence, however,
    # let the asset classifier inspect it before making the final intent decision.
    if (
        (
            not _is_non_asset_category(category)
            and not _is_non_asset_title(title)
        )
        or preliminary_intent == "resource_candidate"
    ):
        detected_category, asset_tags = classify_asset(
            title,
            url,
            source_tags=source_tags,
            description=description_for_classification,
        )

    resource_intent, resource_intent_confidence, resource_intent_evidence = classify_resource_intent(
        item,
        detected_category=detected_category,
    )
    item["resource_intent"] = resource_intent
    item["resource_intent_confidence"] = resource_intent_confidence
    item["resource_intent_evidence"] = resource_intent_evidence

    # Explicit game records remain games. Clear questions/showcases are not
    # promoted to asset/plugin records merely because the forum section says
    # "plugin" or "graphics"; the original category is preserved separately.
    if _is_explicit_game_category(category):
        category_for_type = "ゲーム"
    elif resource_intent == "not_resource":
        category_for_type = "その他"
    elif _is_explicit_plugin_category(category):
        category_for_type = "プラグイン"
    elif detected_category:
        category_for_type = detected_category
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

    # Detailed classification is calculated once and reused for the
    # public subcategory, confidence/evidence fields, and plugin category.
    taxonomy = None
    classification_result = None

    if asset_type in (ASSET_TYPE_SOUND, ASSET_TYPE_PLUGIN, ASSET_TYPE_GRAPHIC):
        taxonomy = (
            "sound"
            if asset_type == ASSET_TYPE_SOUND
            else "plugin"
            if asset_type == ASSET_TYPE_PLUGIN
            else "graphic"
        )

        if taxonomy == "sound":
            classification_result = classify_sound_with_evidence(item)
        else:
            classification_result = classify_taxonomy_with_evidence(
                item,
                taxonomy,
            )

    # 公開DB向けの詳細分類。source_tagsは上書きしない。
    item["subcategory"] = detect_detailed_subcategory(
        item,
        asset_type,
        asset_tags,
        classification_result=classification_result,
    )

    if classification_result is not None:
        if taxonomy == "sound":
            item["sound_type"] = classification_result["sound_type"]

        item["classification_confidence"] = classification_result[
            "classification_confidence"
        ]
        item["classification_status"] = classification_result[
            "classification_status"
        ]
        item["classification_margin"] = classification_result[
            "classification_margin"
        ]
        item["classification_scores"] = classification_result[
            "classification_scores"
        ]
        item["classification_evidence"] = classification_result[
            "classification_evidence"
        ]

        classification_confidence = classification_result[
            "classification_confidence"
        ]
    else:
        # ゲーム・記事・Source Checkなど、
        # graphic / sound / plugin の詳細分類が適用されないItemは
        # 「分類不能」ではなく「対象外」とする。
        classification_confidence = CONFIDENCE_UNKNOWN

    item.setdefault(
        "classification_confidence",
        classification_confidence,
    )

    if asset_type in (
        ASSET_TYPE_GAME,
        ASSET_TYPE_OTHER,
    ):
        item["classification_status"] = "not_applicable"
    else:
        item.setdefault(
            "classification_status",
            detect_classification_status(
                classification_confidence
            ),
        )
    item.setdefault("classification_margin", None)
    item.setdefault("classification_scores", None)
    item.setdefault("classification_evidence", [])
    item.setdefault("classification_note", None)
    item.setdefault("classification_reviewed_at", None)

    if not item.get("sound_type"):
        item["sound_type"] = None

    if asset_type == ASSET_TYPE_PLUGIN:
        # Keep a separate list so callers can update either field safely.
        item["plugin_category"] = list(item["subcategory"])

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
