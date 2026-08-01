from config import (
    VISUSTELLA_RSS,
    VISUSTELLA_SEEN_FILE,
)

from sources.rss import collect_rss

from categories.asset import classify_asset


SEEN_FILE = VISUSTELLA_SEEN_FILE


def get_items(seen):

    return collect_rss(
        url=VISUSTELLA_RSS,
        seen=seen,
        classify=classify_asset,
        source_name="VisuStella",
    )
