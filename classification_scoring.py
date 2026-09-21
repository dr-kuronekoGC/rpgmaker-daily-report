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
