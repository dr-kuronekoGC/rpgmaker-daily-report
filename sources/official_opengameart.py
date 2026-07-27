from config import (
    OPENGAMEART_RSS,
    OPENGAMEART_SEEN_FILE,
)

from sources.rss import collect_rss

from categories import classify_opengameart


SEEN_FILE = OPENGAMEART_SEEN_FILE


def get_items(seen):

    return collect_rss(
        url=OPENGAMEART_RSS,
        seen=seen,
        classify=classify_opengameart,
        source_name="OpenGameArt",
    )
