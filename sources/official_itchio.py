from config import (
    ITCHIO_ASSET_RSS,
    ITCHIO_SEEN_FILE,
)

from sources.rss import collect_rss

from categories import classify_itch


SEEN_FILE = ITCHIO_SEEN_FILE


def get_items(seen):

    return collect_rss(
        url=ITCHIO_ASSET_RSS,
        seen=seen,
        classify=classify_itch,
        source_name="itch.io",
    )
