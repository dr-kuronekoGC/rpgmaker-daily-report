from config import (
    VISUSTELLA_URL,
    VISUSTELLA_SEEN_FILE,
)

from categories.asset import classify_asset

from sources.html_source import collect_html


SEEN_FILE = VISUSTELLA_SEEN_FILE


def is_plugin_page(href):

    return "/plugins/" in href


def get_items(seen):

    return collect_html(
        url=VISUSTELLA_URL,
        seen=seen,
        classify=classify_asset,
        source_name="VisuStella",
        href_filter=is_plugin_page,
    )
