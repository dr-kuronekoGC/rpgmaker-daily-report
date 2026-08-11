# ==========================================
# GameDevMarket
# ==========================================

from config import (
    GAMEDEVMARKET_URL,
    GAMEDEVMARKET_SEEN_FILE,
)

from categories.assets import classify_asset
from sources.html import collect_html


SEEN_FILE = GAMEDEVMARKET_SEEN_FILE


def is_gamedevmarket_item(url):

    return (
        "/category/" not in url
        and url.rstrip("/") != GAMEDEVMARKET_URL.rstrip("/")
    )


def get_items(seen):

    try:

        return collect_html(
            url=GAMEDEVMARKET_URL,
            seen=seen,
            classify=classify_asset,
            selector="a[href]",
            source_name="GameDevMarket",
            href_filter=is_gamedevmarket_item,
        )

    except Exception as e:

        print(
            f"[GameDevMarket] Skip: {e}"
        )

        return [], seen
