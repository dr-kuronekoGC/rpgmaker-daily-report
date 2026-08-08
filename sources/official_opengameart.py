from config import (
    OPENGAMEART_URL,
    OPENGAMEART_SEEN_FILE,
)
from categories.assets import classify_asset
from sources.html import collect_html
SEEN_FILE = OPENGAMEART_SEEN_FILE
def is_opengameart_item(url):
    return (
        "/content/" in url
        or "/art/" in url
    )
def get_items(seen):
    return collect_html(
        url=OPENGAMEART_URL,
        seen=seen,
        classify=classify_asset,
        selector="a[href]",
        source_name="OpenGameArt",
        href_filter=is_opengameart_item,
    )