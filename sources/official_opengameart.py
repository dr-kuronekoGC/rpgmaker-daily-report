from config import (
    OPENGAMEART_URL,
    OPENGAMEART_SEEN_FILE,
)

from categories.asset import classify_asset
from sources.html import collect_html


SEEN_FILE = OPENGAMEART_SEEN_FILE


def get_items(seen):

    return collect_html(
        url=OPENGAMEART_URL,
        seen=seen,
        classify=classify_asset,
        selector="a[href]",
        source_name="OpenGameArt",
    )
