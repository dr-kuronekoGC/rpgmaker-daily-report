# ==========================================
# VisuStella
# ==========================================

from config import (
    VISUSTELLA_URL,
    VISUSTELLA_SEEN_FILE,
)

from categories.assets import classify_asset

from sources.html import collect_html


SEEN_FILE = VISUSTELLA_SEEN_FILE


# ==========================================
# VisuStella Plugin判定
# ==========================================

def is_visustella_plugin(href):

    """
    VisuStellaのRPG Maker MZプラグインページだけを対象にする。
    """

    return (
        "visustellamz.itch.io/" in href
        and href.rstrip("/") != VISUSTELLA_URL.rstrip("/")
    )


# ==========================================
# 分類
# ==========================================

def classify_visustella(
    title,
    url="",
):

    normalized = title.lower().strip()

    # --------------------------------------
    # RPG Maker MZプラグイン
    # --------------------------------------

    if (
        "plugin for rpg maker mz"
        in normalized
    ):
        return "VisuStellaプラグイン"

    # --------------------------------------
    # Access Key / Bundle
    # --------------------------------------

    if (
        normalized.startswith(
            "[access key]"
        )
        and (
            "plugin"
            in normalized
            or "series"
            in normalized
            or "bundle"
            in normalized
        )
    ):
        return "VisuStellaプラグイン"

    return None


# ==========================================
# Main
# ==========================================

def get_items(seen):

    try:

        return collect_html(
            url=VISUSTELLA_URL,
            seen=seen,

            classify=classify_visustella,

            selector="a[href]",

            source_name="VisuStella",

            href_filter=is_visustella_plugin,
        )

    except Exception as e:

        print(
            f"[VisuStella] Error: {e}"
        )

        return [], seen
