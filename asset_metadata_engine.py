# ==========================================
# RPG Maker Engine Detection
# ==========================================

import re

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

# Shared text helpers for engine detection.
def _normalize_text(value):
    if not isinstance(value, str):
        return ""

    return value.lower().strip()


def _contains_any(text, keywords):
    return any(
        keyword in text
        for keyword in keywords
    )

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

    # GitHub branch names can be more specific than the repository name.
    # For example, Triacontane's RPGMakerMV repository uses mz_master for
    # RPG Maker MZ variants; the repository name alone must not misclassify
    # those files as MV.
    if re.search(r"/(?:blob|tree)/mz_master(?:/|$)", url):
        engines = [engine for engine in engines if engine != ENGINE_MV]
        if ENGINE_MZ not in engines:
            engines.append(ENGINE_MZ)
    elif re.search(r"/(?:blob|tree)/mv_master(?:/|$)", url):
        engines = [engine for engine in engines if engine != ENGINE_MZ]
        if ENGINE_MV not in engines:
            engines.append(ENGINE_MV)

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
