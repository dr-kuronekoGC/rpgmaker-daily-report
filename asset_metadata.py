# ==========================================
# Asset Metadata
# ==========================================

import re

from categories.assets import classify_asset
from classification_scoring import (
    classify_sound_with_evidence,
    classify_taxonomy_with_evidence,
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
    """
    Evidence-based detailed taxonomy.

    The source-native metadata is preserved and weighted more heavily
    than free-form description text. Multiple strong categories are allowed
    when an item genuinely belongs to more than one subcategory.
    """

    if asset_type == ASSET_TYPE_GRAPHIC:
        result = classify_taxonomy_with_evidence(item, "graphic")
        return result["categories"]

    if asset_type == ASSET_TYPE_PLUGIN:
        result = classify_taxonomy_with_evidence(item, "plugin")
        return result["categories"]

    if asset_type == ASSET_TYPE_SOUND:
        result = classify_sound_with_evidence(item)
        return [
            result["sound_type"].lower()
            if result["sound_type"]
            else "other"
        ]

    return []

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

    body_text = _normalize_text(
        item.get("body_text")
        or item.get("post_body")
        or item.get("body")
        or item.get("content_text")
        or item.get("content")
        or item.get("text")
        or ""
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
            body_text,
            tags_text,
            url,
        )
    )

    engines = []

    # collectorがページから明示的に取得したエンジン情報は、
    # キーワード再判定より優先して保持する。
    explicit_engine = item.get("engine")

    explicit_engine_map = {
        "RPG Maker MZ": ENGINE_MZ,
        "RPG Maker MV": ENGINE_MV,
        "RPG Maker VX Ace": ENGINE_VX_ACE,
        "RPG Maker VX": ENGINE_VX,
        "RPG Maker XP": ENGINE_XP,
        "RPG Maker 2003": ENGINE_2003,
        "RPG Maker 2000": ENGINE_2000,
        "RPG Maker 95": ENGINE_95,
        "MZ": ENGINE_MZ,
        "MV": ENGINE_MV,
        "VX Ace": ENGINE_VX_ACE,
        "VX": ENGINE_VX,
        "XP": ENGINE_XP,
        "2003": ENGINE_2003,
        "2000": ENGINE_2000,
        "95": ENGINE_95,
    }

    if isinstance(explicit_engine, str):
        mapped_engine = explicit_engine_map.get(
            explicit_engine.strip()
        )
        if mapped_engine:
            engines.append(mapped_engine)

    elif isinstance(explicit_engine, list):
        for value in explicit_engine:
            if not isinstance(value, str):
                continue

            mapped_engine = explicit_engine_map.get(
                value.strip()
            )
            if mapped_engine and mapped_engine not in engines:
                engines.append(mapped_engine)

    # --------------------------------------
    # RPG Maker U2U
    # --------------------------------------

    if (
        _contains_any(
            text,
            (
                "rpg maker u2u",
                "rpgmaker u2u",
                "rpg maker unite 2",
                "rpgmaker unite 2",
            ),
        )
        or re.search(r"(?<![a-z0-9])u2u(?![a-z0-9])", text)
    ):
        engines.append(
            ENGINE_U2U
        )

    # --------------------------------------
    # RPG Maker MZ
    # --------------------------------------

    if (
        _contains_any(
            text,
            (
                "rpg maker mz",
                "rpgmaker mz",
                "rpgツクールmz",
                "rpgツクールmz用",
            ),
        )
        or re.search(r"(?<![a-z0-9])(?:rmmz|rpgmakermz|\[mz\]|\[rmmz\])(?![a-z0-9])", text)
    ):
        engines.append(
            ENGINE_MZ
        )

    # --------------------------------------
    # RPG Maker MV
    # --------------------------------------

    if (
        _contains_any(
            text,
            (
                "rpg maker mv",
                "rpgmaker mv",
                "rpgツクールmv",
                "rpgツクールmv用",
            ),
        )
        or re.search(r"(?<![a-z0-9])(?:rmmv|rpgmakermv|\[mv\]|\[rmmv\])(?![a-z0-9])", text)
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
            "rpgmakermvtrinity",
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

    if (
        _contains_any(
            text,
            (
                "rpg maker vx ace",
                "rpgmaker vx ace",
                "rpgツクールvx ace",
                "rpgツクールvxace",
                "vx ace",
                "vxace",
            ),
        )
        or re.search(r"(?<![a-z0-9])(?:rmvxa|rpgmakervxa|rpgmakervxace|vxa|\[vxa\]|\[rmvxa\]|\[vx ace\])(?![a-z0-9])", text)
    ):
        engines.append(
            ENGINE_VX_ACE
        )

    # --------------------------------------
    # RPG Maker VX
    # --------------------------------------

    explicit_vx_alias = re.search(
        r"(?<![a-z0-9])(?:rmvx|rpgmakervx|\[vx\]|\[rmvx\]|vx(?=[/\]]))(?![a-z0-9])",
        text,
    )

    if explicit_vx_alias or (
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

    if (
        _contains_any(
            text,
            (
                "rpg maker xp",
                "rpgmaker xp",
                "rpgツクールxp",
            ),
        )
        or re.search(r"(?<![a-z0-9])(?:rmxp|rpgmakerxp|\[xp\]|\[rmxp\]|xp(?=[/\]]))(?![a-z0-9])", text)
    ):
        engines.append(
            ENGINE_XP
        )

    # --------------------------------------
    # RPG Maker 2003
    # --------------------------------------

    if (
        _contains_any(
            text,
            (
                "rpg maker 2003",
                "rpgmaker 2003",
                "rpgツクール2003",
            ),
        )
        or re.search(r"(?<![a-z0-9])(?:rm?2k3|rpgmaker2003|2k3|\[2k3\]|\[rm2k3\])(?![a-z0-9])", text)
    ):
        engines.append(
            ENGINE_2003
        )

    # --------------------------------------
    # RPG Maker 2000
    # --------------------------------------

    if (
        _contains_any(
            text,
            (
                "rpg maker 2000",
                "rpgmaker 2000",
                "rpgツクール2000",
            ),
        )
        or re.search(r"(?<![a-z0-9])(?:rm?2k|rpgmaker2000|2k|\[2k\]|\[rm2k\])(?![a-z0-9])", text)
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
            "rpgmaker95",
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

    if (
        _contains_any(
            text,
            (
                "rpg maker unite",
                "rpgmaker unite",
                "rpgツクールunite",
                "rpgツクール unite",
            ),
        )
        or re.search(r"(?<![a-z0-9])(?:rm?unite|\[unite\]|\[rmunite\])(?![a-z0-9])", text)
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
# Classification guards
# ==========================================

def _is_non_asset_category(category):
    text = _normalize_text(category)

    non_asset_keywords = (
        "質問",
        "相談",
        "tips",
        "tip",
        "help",
        "question",
        "questions",
        "discussion",
        "news",
        "情報",
        "公式情報",
        "サイト更新",
        "site update",
        "sourcecheck",
    )

    return any(
        keyword in text
        for keyword in non_asset_keywords
    )


def _is_non_asset_title(title):
    text = _normalize_text(title)

    # 質問・解説・作品紹介を素材として誤登録しないための保護。
    # これらは「音楽」「sound」等の単語を含んでも、
    # 素材そのものとは限らない。
    non_asset_keywords = (
        "question",
        "questions",
        "need help",
        "help",
        "how do",
        "study",
        "audiobook",
        "showcase",
        "showcasing",
        "my project",
        "project showcase",
        "compatibility",
        "compatible",
        # "engine" alone is common in actual plugin/resource titles
        # (e.g. "ABS Engine Pro"), so it must not be a blanket exclusion.
        # Likewise, "video" alone can refer to a plugin demo/release page.
        # Keep only explicit gameplay/process media signals.
        "gameplay video",
        "making-of video",
        "process video",
        "trailer",
        "ゲーム",
        "エンジン",
        "プロジェクト",
        "互換",
        "について手伝",
        "手伝って",
    )

    return any(
        keyword in text
        for keyword in non_asset_keywords
    )


def _is_explicit_plugin_category(category):
    text = _normalize_text(category)

    return (
        text in ("plugin", "plugins", "プラグイン")
        or "プラグイン" in text
    )


def _is_explicit_game_category(category):
    text = _normalize_text(category)

    return (
        text in ("game", "games", "ゲーム")
        or "ゲーム" in text
    )


def classify_resource_intent(item, detected_category=None):
    """
    Resource-intent triage, deliberately separate from detailed taxonomy.

    Returns (intent, confidence, evidence), where intent is:
      - resource_candidate: concrete release/distribution or a clear asset signal
      - not_resource: clear question/showcase/news context without a deliverable
      - uncertain: insufficient evidence to decide safely

    Price, paid status, or an external storefront are never negative signals.
    """
    title = str(item.get("title") or "")
    category = str(item.get("category") or "")
    source_tags = item.get("source_tags", [])
    tags = item.get("tags", [])
    if not isinstance(source_tags, list):
        source_tags = []
    if not isinstance(tags, list):
        tags = []

    body_parts = []
    for field in ("description", "body_text", "post_body", "body", "content_text", "content", "text"):
        value = item.get(field)
        if isinstance(value, str) and value.strip():
            body_parts.append(value.strip())

    combined = " ".join(
        [title, category, str(item.get("url") or "")]
        + [str(x) for x in source_tags + tags]
        + body_parts
    ).lower()

    # Only concrete distribution/release wording is a strong positive signal.
    distribution_signals = (
        "download here",
        "download link",
        "available for download",
        "download the plugin",
        "download the resource",
        "downloadable resource",
        "downloadable asset",
        "free to use",
        "asset pack",
        "resource pack",
        "plugin release",
        "released",
        "release available",
        "get it here",
        "配布中",
        "ダウンロードはこちら",
        "ダウンロードリンク",
        "素材配布",
        "公開しました",
        "配布ページ",
    )
    distribution_hits = [word for word in distribution_signals if word in combined]

    # Explicitly identified games, official notices and source-update entries
    # are not resource records by themselves; a linked release can still qualify.
    category_text = category.lower()
    is_game = _is_explicit_game_category(category)
    is_site_notice = _is_non_asset_category(category)

    title_guard = _is_non_asset_title(title)
    category_guard = is_site_notice
    guarded_context = title_guard or category_guard

    if distribution_hits:
        return (
            "resource_candidate",
            "medium",
            [{"field": "body_or_metadata", "signal": signal} for signal in distribution_hits[:5]],
        )

    if is_game:
        return ("not_resource", "high", [{"field": "category", "signal": "explicit_game"}])

    # Question/showcase/discussion terms are negative only when no concrete
    # distribution evidence was found. This does not exclude paid resources.
    if guarded_context:
        signal = "question_or_showcase_title" if title_guard else "non_resource_category"
        return ("not_resource", "medium", [{"field": "title" if title_guard else "category", "signal": signal}])

    if detected_category:
        return (
            "resource_candidate",
            "medium",
            [{"field": "title_url_or_tags", "signal": "asset_classifier_match", "category": detected_category}],
        )

    resource_tags = ("asset", "assets", "resource", "resources", "plugin", "plugins", "素材", "プラグイン")
    tag_hits = [str(tag) for tag in source_tags + tags if any(word in str(tag).lower() for word in resource_tags)]
    if tag_hits:
        return (
            "uncertain",
            "low",
            [{"field": "source_tags_or_tags", "signal": tag} for tag in tag_hits[:5]],
        )

    return ("uncertain", "unknown", [])


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

    # 公開DB向けの詳細分類。source_tagsは上書きしない。
    item["subcategory"] = detect_detailed_subcategory(
        item,
        asset_type,
        asset_tags,
    )

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
