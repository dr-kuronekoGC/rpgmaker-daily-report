# ==========================================
# Asset Metadata
# ==========================================

from categories.assets import classify_asset
from classification_scoring import classify_sound_with_evidence


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

def detect_detailed_subcategory(item, asset_type, asset_tags):
    title = _normalize_text(item.get("title", ""))
    description = _normalize_text(item.get("description", ""))
    source_tags = item.get("source_tags", [])
    source_text = " ".join(_normalize_text(x) for x in source_tags if isinstance(x, str))
    text = " ".join((title, description, source_text, " ".join(asset_tags or [])))
    result = []

    if asset_type == ASSET_TYPE_GRAPHIC:
        for name, keywords in GRAPHIC_SUBCATEGORY_KEYWORDS.items():
            if _contains_keyword(text, keywords) and name not in result:
                result.append(name)
        if not result:
            result.append("other")

    elif asset_type == ASSET_TYPE_SOUND:
        if _contains_keyword(text, ("bgm", "music", "soundtrack", "ost")):
            result.append("music")
        elif _contains_keyword(text, ("bgs", "background sound")):
            result.append("ambient")
        elif _contains_keyword(text, ("me", "music effect", "jingle", "fanfar")):
            result.append("music_effect")
        elif _contains_keyword(text, ("se", "sfx", "sound effect", "sound effects")):
            result.append("sound_effect")
        else:
            result.append("other")

    elif asset_type == ASSET_TYPE_PLUGIN:
        for name, keywords in PLUGIN_CATEGORY_KEYWORDS.items():
            if _contains_keyword(text, keywords) and name not in result:
                result.append(name)
        if not result:
            result.append("other")

    return result

def detect_sound_type(item):
    """
    サウンド素材の詳細分類。

    明示的なBGM/BGS/ME/SE表記を優先する。
    「music」「soundtrack」のような一般的な表現だけの場合は
    BGM候補として扱うが、確定とはせず確認対象にする。
    """
    text = " ".join(
        (
            _normalize_text(item.get("title", "")),
            _normalize_text(item.get("description", "")),
            " ".join(_normalize_text(x) for x in item.get("source_tags", []) if isinstance(x, str)),
            " ".join(_normalize_text(x) for x in item.get("asset_tags", []) if isinstance(x, str)),
        )
    )

    if _contains_keyword(text, ("bgm", "background music")):
        return "BGM"

    if _contains_keyword(text, ("bgs", "background sound")):
        return "BGS"

    if _contains_keyword(text, ("me", "music effect", "jingle", "fanfar")):
        return "ME"

    if _contains_keyword(text, ("se", "sfx", "sound effect", "sound effects")):
        return "SE"

    if _contains_keyword(text, ("music", "soundtrack", "ost")):
        return "BGM"

    return None


def detect_sound_classification_confidence(item):
    """
    sound_typeの判定根拠を確認する。

    high:
        BGM/BGS/ME/SEなどの分類語が明示されている。
    medium:
        music / soundtrack / OSTなどからBGM候補と推定した。
    low:
        サウンド素材だが詳細種別を判断できない。
    """
    text = " ".join(
        (
            _normalize_text(item.get("title", "")),
            _normalize_text(item.get("description", "")),
            " ".join(_normalize_text(x) for x in item.get("source_tags", []) if isinstance(x, str)),
            " ".join(_normalize_text(x) for x in item.get("asset_tags", []) if isinstance(x, str)),
        )
    )

    if _contains_keyword(
        text,
        ("bgm", "background music", "bgs", "background sound",
         "me", "music effect", "jingle", "fanfar",
         "se", "sfx", "sound effect", "sound effects"),
    ):
        return CONFIDENCE_HIGH

    if _contains_keyword(text, ("music", "soundtrack", "ost")):
        return CONFIDENCE_MEDIUM

    return CONFIDENCE_LOW


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

    # 公開DB向けの詳細分類。source_tagsは上書きしない。
    item["subcategory"] = detect_detailed_subcategory(
        item,
        asset_type,
        asset_tags,
    )

    if asset_type == ASSET_TYPE_SOUND:
        sound_result = classify_sound_with_evidence(item)

        item["sound_type"] = sound_result["sound_type"]
        item["classification_confidence"] = sound_result[
            "classification_confidence"
        ]
        item["classification_status"] = sound_result[
            "classification_status"
        ]
        item["classification_margin"] = sound_result[
            "classification_margin"
        ]
        item["classification_scores"] = sound_result[
            "classification_scores"
        ]
        item["classification_evidence"] = sound_result[
            "classification_evidence"
        ]

        classification_confidence = sound_result[
            "classification_confidence"
        ]

    elif asset_type == ASSET_TYPE_PLUGIN:
        classification_confidence = (
            CONFIDENCE_HIGH
            if item.get("subcategory")
            and item.get("subcategory") != ["other"]
            else CONFIDENCE_LOW
        )
    elif asset_type == ASSET_TYPE_GRAPHIC:
        classification_confidence = (
            CONFIDENCE_HIGH
            if item.get("subcategory")
            and item.get("subcategory") != ["other"]
            else CONFIDENCE_LOW
        )
    else:
        classification_confidence = CONFIDENCE_UNKNOWN

    item.setdefault(
        "classification_confidence",
        classification_confidence,
    )
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
        item["plugin_category"] = detect_detailed_subcategory(
            item,
            asset_type,
            asset_tags,
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
