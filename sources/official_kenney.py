from config import (
    KENNEY_RSS,
    KENNEY_SEEN_FILE,
)

from sources.rss import collect_rss

from categories import classify_kenney


SEEN_FILE = KENNEY_SEEN_FILE


def get_items(seen):

    return collect_rss(
        url=KENNEY_RSS,
        seen=seen,
        classify=classify_kenney,
        source_name="Kenney",
    )
