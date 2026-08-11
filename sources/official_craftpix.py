# ==========================================
# CraftPix
# ==========================================

from config import (
    CRAFTPIX_RSS,
    CRAFTPIX_SEEN_FILE,
)

from sources.html import collect_html

from categories.assets import classify_asset


SEEN_FILE = CRAFTPIX_SEEN_FILE


def is_craftpix_item(url):

    excluded = (
        "/category/",
        "/tag/",
        "/author/",
        "/page/",
    )

    if any(
        path in url
        for path in excluded
    ):
        return False

    return (
        "craftpix.net/" in url
        and url.rstrip("/") != CRAFTPIX_RSS.rstrip("/")
    )


def get_items(seen):

    try:

        return collect_html(
            url=CRAFTPIX_RSS,
            seen=seen,
            classify=classify_asset,
            selector="a",
            source_name="CraftPix",
            href_filter=is_craftpix_item,
        )

    except Exception as e:

        print(
            f"[CraftPix] Skip: {e}"
        )

        return [], seen
