from config import (
    GAMEDEVMARKET_URL,
    GAMEDEVMARKET_SEEN_FILE,
)

from categories.assets import classify_asset

from sources.html import collect_html


SEEN_FILE = GAMEDEVMARKET_SEEN_FILE


def is_asset_url(url):

    return "/asset/" in url


def get_items(seen):

    try:

        return collect_html(
            url=GAMEDEVMARKET_URL,
            seen=seen,
            classify=classify_asset,
            selector="a[href]",
            source_name="GameDevMarket",
            href_filter=is_asset_url,
        )

    except Exception as e:

        print(
            f"[GameDevMarket] Error: {e}"
        )

        return [], seen