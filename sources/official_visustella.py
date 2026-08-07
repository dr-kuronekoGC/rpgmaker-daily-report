from config import (
    VISUSTELLA_URL,
    VISUSTELLA_SEEN_FILE,
)

from categories.assets import classify_asset

from sources.html import collect_html


SEEN_FILE = VISUSTELLA_SEEN_FILE


def is_plugin_page(href):

    return "/plugins/" in href


def get_items(seen):

    try:

        return collect_html(
            url=VISUSTELLA_URL,
            seen=seen,
            classify=classify_asset,
            selector="a[href]",
            source_name="VisuStella",
            href_filter=is_plugin_page,
        )

    except Exception as e:

        print(
            f"[VisuStella] Error: {e}"
        )

        return [], seen
