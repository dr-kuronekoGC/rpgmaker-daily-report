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


from classification_rules import (
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_LOW,
    CONFIDENCE_UNKNOWN,
    SOUND_TYPES,
    SHORT_ABBREVIATIONS,
    FIELD_WEIGHTS,
    SOUND_PATTERNS,
    GRAPHIC_PATTERNS,
    PLUGIN_PATTERNS,
)

def _contains_short_abbreviation(text, abbreviation):
    """大文字のRPG Maker略語として現れているかを判定する。"""
    if abbreviation not in SHORT_ABBREVIATIONS:
        return False

    raw = str(text or "")
    pattern = r"(?<![A-Za-z0-9])" + re.escape(abbreviation) + r"(?![A-Za-z0-9])"
    return re.search(pattern, raw) is not None


# Strong evidence is weighted by where it appears.
# Source-native tags are usually more reliable than free-form descriptions.
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


def _field_raw_text(item, field):
    value = item.get(field)

    if isinstance(value, list):
        return " ".join(str(x) for x in value if x is not None)

    if value is None:
        return ""

    return str(value)


def _score_sound_type(item, sound_type, fields=None):
    if fields is None:
        fields = _field_values(item)
    score = 0
    evidence = []

    for field, weight in FIELD_WEIGHTS.items():
        text = fields[field]
        if not text:
            continue

        for pattern, base_score, label in SOUND_PATTERNS[sound_type]:
            # SEの明示表記だけは大文字小文字を区別する。
            # それ以外の音関連語は従来どおり大文字小文字を区別しない。
            if label == f"explicit:{sound_type}":
                search_text = _field_raw_text(item, field)
                if _contains_short_abbreviation(search_text, sound_type):
                    points = base_score + max(weight - 3, 0)
                    score += points
                    evidence.append({
                        "field": field,
                        "points": points,
                        "evidence": label,
                    })
                continue

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
    fields = _field_values(item)

    for sound_type in SOUND_TYPES:
        score, evidence = _score_sound_type(item, sound_type, fields)
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


def _apply_source_category_hint(scores, evidence, item, taxonomy):
    """
    Oniromancieのカテゴリはサイト側の分類なので、本文キーワードより
    強い補助証拠として扱う。ただし完全固定にはせず、他の明確な証拠を
    上書きしない。
    """
    tags = item.get("source_tags", [])

    if not isinstance(tags, list):
        return

    source_text = " ".join(str(tag).lower() for tag in tags)

    aliases = {
        "戦闘": "battle",
        "combat": "battle",
        "メッセージ": "messages_dialogue",
        "messages": "messages_dialogue",
        "マップ": "map_events",
        "maps": "map_events",
        "menu": "menu_ui",
        "メニュー": "menu_ui",
        "son et musique": "audio",
        "音楽・サウンド": "audio",
        "musique": "audio",
    }

    target = None
    for alias, category in aliases.items():
        if alias in source_text:
            target = category
            break

    if not target or target not in scores:
        return

    scores[target] += 6
    evidence[target].append({
        "field": "source_tags",
        "keyword": "source_category",
        "points": 6,
    })


def classify_taxonomy_with_evidence(item, taxonomy):
    if taxonomy == "graphic":
        patterns = GRAPHIC_PATTERNS
    elif taxonomy == "plugin":
        patterns = PLUGIN_PATTERNS
    else:
        raise ValueError(f"Unsupported taxonomy: {taxonomy}")

    scores, evidence = _score_taxonomy(item, patterns)

    _apply_source_category_hint(
        scores,
        evidence,
        item,
        taxonomy,
    )

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
