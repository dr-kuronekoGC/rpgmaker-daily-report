from config import (
    CRAFTPIX_RSS,
    CRAFTPIX_SEEN_FILE,
)

from sources.rss import collect_rss

from categories import classify_craftpix


SEEN_FILE = CRAFTPIX_SEEN_FILE


def get_items(seen):

    return collect_rss(
        url=CRAFTPIX_RSS,
        seen=seen,
        classify=classify_craftpix,
        source_name="CraftPix",
    )
