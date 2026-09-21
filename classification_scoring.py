# ==========================================
# Classification Scoring
# ==========================================
"""
Evidence-based classification for detailed RPG Maker taxonomy.

The classifier deliberately separates:
- classification result
- evidence strength
- review status

A weak guess is preferable to false precision.
"""

import re


CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"
CONFIDENCE_UNKNOWN = "unknown"


SOUND_TYPES = ("BGM", "BGS", "ME", "SE")


# Strong evidence is weighted by where it appears.
# Source-native tags are usually more reliable than free-form descriptions.
FIELD_WEIGHTS = {
    "title": 5,
    "source_tags": 4,
    "category": 3,
    "description": 3,
    "url": 2,
    "asset_tags": 2,
}


SOUND_PATTERNS = {
    "BGM": (
        (r"\bbgm\b", 5, "explicit:BGM"),
        (r"background music", 5, "explicit:background music"),
        (r"\btheme music\b", 4, "theme music"),
        (r"\bsoundtrack\b", 3, "soundtrack"),
        (r"\bost\b", 3, "OST"),
        (r"\bmusic\b", 1, "generic:music"),
        (r"音楽", 4, "ja:音楽"),
        (r"BGM", 5, "ja:BGM"),
    ),
    "BGS": (
        (r"\bbgs\b", 5, "explicit:BGS"),
        (r"background sound", 5, "background sound"),
        (r"ambient sound", 4, "ambient sound"),
        (r"ambience", 4, "ambience"),
        (r"environmental sound", 4, "environmental sound"),
        (r"環境音", 5, "ja:環境音"),
        (r"BGS", 5, "ja:BGS"),
    ),
    "ME": (
        (r"\bme\b", 5, "explicit:ME"),
        (r"music effect", 5, "music effect"),
        (r"jingle", 4, "jingle"),
        (r"fanfare", 4, "fanfare"),
        (r"victory", 3, "victory"),
        (r"defeat", 3, "defeat"),
        (r"game over", 3, "game over"),
        (r"ジングル", 4, "ja:ジングル"),
        (r"ファンファーレ", 4, "ja:ファンファーレ"),
        (r"ME", 5, "ja:ME"),
    ),
    "SE": (
        (r"\bse\b", 5, "explicit:SE"),
        (r"\bsfx\b", 5, "SFX"),
        (r"sound effect", 5, "sound effect"),
        (r"sound effects", 5, "sound effects"),
        (r"foley", 4, "foley"),
        (r"sound fx", 4, "sound fx"),
        (r"効果音", 5, "ja:効果音"),
        (r"SE", 5, "ja:SE"),
    ),
}


def _field_text(item, field):
    value = item.get(field)

    if isinstance(value, list):
        return " ".join(str(x) for x in value if x is not None).lower()

    if value is None:
        return ""

    return str(value).lower()


def _field_values(item):
    return {
        field: _field_text(item, field)
        for field in FIELD_WEIGHTS
    }


def _score_sound_type(item, sound_type):
    fields = _field_values(item)
    score = 0
    evidence = []

    for field, weight in FIELD_WEIGHTS.items():
        text = fields[field]
        if not text:
            continue

        for pattern, base_score, label in SOUND_PATTERNS[sound_type]:
            if re.search(pattern, text, flags=re.IGNORECASE):
                points = base_score + max(weight - 3, 0)
                score += points
                evidence.append({
                    "field": field,
                    "points": points,
                    "evidence": label,
                })

    return score, evidence


def classify_sound_with_evidence(item):
    """
    Return the best sound type plus transparent evidence.

    Rules:
    - high/auto: strong evidence and a clear lead
    - medium/needs_review: plausible classification but not sufficiently clear
    - low/needs_review: weak or conflicting evidence
    - unknown/needs_review: no useful evidence

    We intentionally do not force BGM for every item containing "music".
    """

    scores = {}

    for sound_type in SOUND_TYPES:
        score, evidence = _score_sound_type(item, sound_type)
        scores[sound_type] = {
            "score": score,
            "evidence": evidence,
        }

    ranked = sorted(
        SOUND_TYPES,
        key=lambda x: scores[x]["score"],
        reverse=True,
    )

    best = ranked[0]
    second = ranked[1]

    best_score = scores[best]["score"]
    second_score = scores[second]["score"]
    margin = best_score - second_score

    if best_score >= 9 and margin >= 4:
        confidence = CONFIDENCE_HIGH
        status = "auto"
    elif best_score >= 5 and margin >= 2:
        confidence = CONFIDENCE_MEDIUM
        status = "needs_review"
    elif best_score > 0:
        confidence = CONFIDENCE_LOW
        status = "needs_review"
    else:
        confidence = CONFIDENCE_UNKNOWN
        status = "needs_review"

    return {
        "sound_type": best if best_score > 0 else None,
        "classification_confidence": confidence,
        "classification_status": status,
        "classification_margin": margin,
        "classification_scores": {
            sound_type: scores[sound_type]["score"]
            for sound_type in SOUND_TYPES
        },
        "classification_evidence": scores[best]["evidence"],
    }


# ==========================================
# Graphic / Plugin detailed classification
# ==========================================

GRAPHIC_PATTERNS = {
    "character": (("character", 5), ("charset", 5), ("character sheet", 6), ("キャラクター", 5)),
    "sv_character": (("sv character", 6), ("sv battler", 6), ("side-view character", 6), ("sv戦闘", 6), ("svキャラ", 6)),
    "enemy_battler": (("enemy battler", 6), ("enemy sprite", 5), ("monster sprite", 5), ("enemy", 5), ("敵キャラ", 5), ("敵キャラクター", 5)),
    "face": (("faceset", 6), ("face set", 6), ("face graphic", 6), ("face graphics", 6), ("顔グラフィック", 6)),
    "bust": (("bust", 5), ("bustup", 6), ("bust up", 6), ("バストアップ", 6)),
    "full_art": (("full art", 6), ("key art", 6), ("illustration", 4), ("concept art", 4), ("全身", 5)),
    "tileset": (("tileset", 6), ("tile set", 6), ("tilemap", 5), ("tilesheet", 6), ("タイルセット", 6), ("マップチップ", 6)),
    "battle_background": (("battleback", 6), ("battle background", 6), ("戦闘背景", 6)),
    "parallax": (("parallax", 6), ("遠景", 6), ("パララックス", 6)),
    "animation": (("animation", 5), ("effekseer", 6), ("アニメーション", 6)),
    "icon": (("icon", 5), ("icons", 5), ("icon set", 6), ("icon pack", 6), ("アイコン", 5)),
    "ui_system": (("ui", 5), ("user interface", 6), ("window skin", 6), ("windowskin", 6), ("system graphic", 6), ("システム", 4), ("ui素材", 6)),
    "title": (("title screen", 6), ("title graphic", 6), ("title logo", 6), ("タイトル", 4)),
}

PLUGIN_PATTERNS = {
    "system_core": (("core", 5), ("system", 4), ("utility", 3), ("engine", 3), ("コア", 5), ("システム", 4)),
    "battle": (("battle", 5), ("combat", 5), ("action battle", 6), ("atb", 6), ("ctb", 6), ("戦闘", 5), ("バトル", 5)),
    "skills_states": (("skill", 5), ("skills", 5), ("state", 5), ("states", 5), ("buff", 5), ("debuff", 5), ("スキル", 5), ("ステート", 5)),
    "menu_ui": (("menu", 5), ("hud", 5), ("ui", 5), ("window", 4), ("status menu", 6), ("メニュー", 5), ("ウィンドウ", 4)),
    "items_equipment": (("item", 5), ("items", 5), ("equipment", 5), ("equip", 5), ("アイテム", 5), ("装備", 5)),
    "shop": (("shop", 6), ("merchant", 5), ("ショップ", 6), ("店", 4)),
    "character_party": (("party", 5), ("actor", 5), ("actors", 5), ("formation", 5), ("パーティ", 5), ("アクター", 5), ("隊列", 5)),
    "quest": (("quest", 6), ("journal", 5), ("mission", 5), ("クエスト", 6), ("ミッション", 5)),
    "map_events": (("map", 4), ("event", 5), ("events", 5), ("movement", 4), ("マップ", 4), ("イベント", 5)),
    "save_load": (("save", 5), ("load", 5), ("autosave", 6), ("セーブ", 5), ("ロード", 5)),
    "messages_dialogue": (("message", 5), ("messages", 5), ("dialogue", 5), ("dialog", 5), ("text", 3), ("メッセージ", 5), ("会話", 5)),
    "audio": (("audio", 5), ("sound", 5), ("bgm", 6), ("bgs", 6), ("se", 6), ("sfx", 6), ("音声", 5), ("音楽", 5)),
    "graphics": (("graphic", 5), ("graphics", 5), ("sprite", 5), ("picture", 5), ("animation", 5), ("画像", 5), ("スプライト", 5)),
    "database": (("database", 6), ("notetag", 6), ("db", 6), ("データベース", 6), ("メモタグ", 6)),
    "development_debug": (("debug", 6), ("developer", 5), ("development", 5), ("test", 3), ("console", 5), ("デバッグ", 6), ("開発", 5)),
    "network_external": (("network", 6), ("api", 6), ("http", 6), ("web", 5), ("discord", 5), ("integration", 5), ("external", 4), ("連携", 5)),
}


def _score_taxonomy(item, patterns):
    fields = _field_values(item)
    scores = {}
    evidence = {}

    for category, keywords in patterns.items():
        score = 0
        hits = []

        for field, weight in FIELD_WEIGHTS.items():
            value = fields[field]
            if not value:
                continue

            for keyword, base_score in keywords:
                if _contains_phrase(value, keyword):
                    points = base_score + max(weight - 3, 0)
                    score += points
                    hits.append({
                        "field": field,
                        "keyword": keyword,
                        "points": points,
                    })

        scores[category] = score
        evidence[category] = hits

    return scores, evidence


def _contains_phrase(text, phrase):
    import re

    phrase = str(phrase or "").strip().lower()
    if not phrase:
        return False

    # Japanese terms do not need word boundaries.
    if re.search(r"[^a-z0-9]", phrase):
        return phrase in text

    pattern = r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])"
    return re.search(pattern, text) is not None


def classify_taxonomy_with_evidence(item, taxonomy):
    if taxonomy == "graphic":
        patterns = GRAPHIC_PATTERNS
    elif taxonomy == "plugin":
        patterns = PLUGIN_PATTERNS
    else:
        raise ValueError(f"Unsupported taxonomy: {taxonomy}")

    scores, evidence = _score_taxonomy(item, patterns)

    ranked = sorted(
        scores,
        key=lambda key: scores[key],
        reverse=True,
    )

    if not ranked or scores[ranked[0]] == 0:
        return {
            "categories": ["other"],
            "classification_confidence": CONFIDENCE_UNKNOWN,
            "classification_status": "needs_review",
            "classification_scores": scores,
            "classification_evidence": [],
            "classification_margin": 0,
        }

    best = ranked[0]
    second_score = scores[ranked[1]] if len(ranked) > 1 else 0
    best_score = scores[best]
    margin = best_score - second_score

    if best_score >= 10 and margin >= 4:
        confidence = CONFIDENCE_HIGH
        status = "auto"
    elif best_score >= 6 and margin >= 2:
        confidence = CONFIDENCE_MEDIUM
        status = "needs_review"
    else:
        confidence = CONFIDENCE_LOW
        status = "needs_review"

    # Graphics can legitimately have multiple simultaneous subcategories
    # (e.g. character + full art). Plugins can also affect several areas,
    # but only retain strong, near-top candidates to avoid tag explosion.
    categories = [
        name
        for name in ranked
        if scores[name] >= 6
        and scores[name] >= best_score - 3
    ]

    if not categories:
        categories = [best]

    selected_evidence = []
    for name in categories:
        selected_evidence.extend(evidence[name])

    return {
        "categories": categories,
        "classification_confidence": confidence,
        "classification_status": status,
        "classification_scores": scores,
        "classification_evidence": selected_evidence,
        "classification_margin": margin,
    }
