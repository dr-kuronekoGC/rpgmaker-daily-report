# ==========================================
# itch.io Assets
# ==========================================

from config import (
    ITCHIO_ASSET_RSS,
    ITCHIO_SEEN_FILE,
)

from sources.rss import collect_rss

from categories.assets import classify_asset


SEEN_FILE = ITCHIO_SEEN_FILE


def get_items(seen):

    try:

        return collect_rss(
            url=ITCHIO_ASSET_RSS,
            seen=seen,
            classify=classify_asset,
            source_name="itch.io",
        )

    except Exception as e:

        print(
            f"[itch.io] Skip: {e}"
        )

        return [], seen
