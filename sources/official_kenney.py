# ==========================================
# Kenney
# ==========================================

from config import (
    KENNEY_RSS,
    KENNEY_SEEN_FILE,
)

from sources.html import collect_html

from categories.assets import classify_asset


SEEN_FILE = KENNEY_SEEN_FILE


def is_kenney_item(url):

    excluded = (
        "/assets/tag:",
        "/assets/category:",
        "/assets/search:",
    )

    if any(
        path in url
        for path in excluded
    ):
        return False

    return (
        "/assets/" in url
        and url.rstrip("/") != KENNEY_RSS.rstrip("/")
    )


def get_items(seen):

    try:

        return collect_html(
            url=KENNEY_RSS,
            seen=seen,
            classify=classify_asset,
            selector="a",
            source_name="Kenney",
            href_filter=is_kenney_item,
        )

    except Exception as e:

        print(
            f"[Kenney] Skip: {e}"
        )

        return [], seen
