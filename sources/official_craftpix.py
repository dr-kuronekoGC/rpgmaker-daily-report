from config import (
    CRAFTPIX_RSS,
    CRAFTPIX_SEEN_FILE,
)

from sources.rss import collect_rss

from categories.assets import classify_asset


SEEN_FILE = CRAFTPIX_SEEN_FILE


def get_items(seen):

    return collect_rss(
        url=CRAFTPIX_RSS,
        seen=seen,
        classify=classify_asset,
        source_name="CraftPix",
    )
