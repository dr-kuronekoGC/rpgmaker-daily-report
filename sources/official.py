from config import (
    OFFICIAL_NEWS_URL,
    OFFICIAL_SEEN_FILE,
)

from categories import classify_official

from sources.html import collect_html

SEEN_FILE = OFFICIAL_SEEN_FILE


def get_items(seen):

    return collect_html(

        url=OFFICIAL_NEWS_URL,

        seen=seen,

        classify=classify_official,

        selector="h3",

        source_name="Official",

    )
