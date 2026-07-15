from config import (
    RSS_URL,
    REDDIT_SEEN_FILE,
)

from categories import classify_reddit

from sources.rss import collect_rss


SEEN_FILE = REDDIT_SEEN_FILE


def get_items(seen):

    return collect_rss(
        url=RSS_URL,
        seen=seen,
        classify=classify_reddit,
        source_name="Reddit",
    )
