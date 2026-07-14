from config import (
    FORUM_URL,
    FORUM_SEEN_FILE,
)

from categories import classify_forum

from sources.html import collect_html

SEEN_FILE = FORUM_SEEN_FILE


def get_items(seen):

    return collect_html(
        url=FORUM_URL,
        seen=seen,
        classify=classify_forum,
        selector=".structItem-title",
        source_name="Forum",
    )
