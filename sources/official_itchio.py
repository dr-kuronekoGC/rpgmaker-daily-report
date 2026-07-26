from config import (
    ITCHIO_URL,
    ITCHIO_SEEN_FILE,
)

from categories import classify_itchio

from sources.rss import collect_rss


SEEN_FILE = ITCHIO_SEEN_FILE


def get_items(seen):

    return collect_rss(
        url=ITCHIO_URL,
        seen=seen,
        classify=classify_itchio,
        source_name="itch.io",
    )
