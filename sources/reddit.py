from config import (
    RSS_URL,
    REDDIT_SEEN_FILE,
)

from categories import classify_reddit
from sources.base import get_feed

SEEN_FILE = REDDIT_SEEN_FILE

def get_items(seen):

    feed = get_feed(RSS_URL)
    print(f"[Reddit] RSS: {len(feed.entries)}件")

    new_seen = seen.copy()
    adopted_items = []

    for entry in feed.entries:

        url = entry.link

        if url in seen:
            continue

        new_seen.append(url)

        category = classify_reddit(entry.title)

        if category is None:
            continue

        adopted_items.append(
            {
                "title": entry.title,
                "url": url,
                "category": category,
            }
        )

        print(
            f"[Reddit][{category}] {entry.title}"
        )

    print(f"[Reddit] New: {len(adopted_items)}")

    return adopted_items, new_seen
