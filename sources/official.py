from config import OFFICIAL_NEWS_URL

from categories import classify_official

from sources.html_source import collect_h3_items


def get_items(seen):

    return collect_h3_items(
        url=OFFICIAL_NEWS_URL,
        seen=seen,
        classifier=classify_official,
        source_name="Official",
    )
