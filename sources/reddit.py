import feedparser

from config import RSS_URL
from categories import classify_reddit


def get_items(seen):

    feed = feedparser.parse(RSS_URL)

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
