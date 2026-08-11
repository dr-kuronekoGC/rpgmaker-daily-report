# ==========================================
# itch.io Assets
# ==========================================

from config import (
    ITCHIO_ASSET_RSS,
    ITCHIO_SEEN_FILE,
)

from sources.html import collect_html

from categories.assets import classify_asset


SEEN_FILE = ITCHIO_SEEN_FILE


def is_itchio_item(url):

    excluded = (
        "/tag/",
        "/games/",
        "/game-assets/",
        "/search",
        "/jam/",
        "/user/",
    )

    if any(
        path in url
        for path in excluded
    ):
        return False

    return (
        "itch.io/" in url
        and url.rstrip("/") != ITCHIO_ASSET_RSS.rstrip("/")
    )


def get_items(seen):

    try:

        return collect_html(
            url=ITCHIO_ASSET_RSS,
            seen=seen,
            classify=classify_asset,
            selector="a",
            source_name="itch.io",
            href_filter=is_itchio_item,
        )

    except Exception as e:

        print(
            f"[itch.io] Skip: {e}"
        )

        return [], seen
