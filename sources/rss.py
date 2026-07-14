from sources.base import get_feed


def collect_rss(
    *,
    url,
    seen,
    classify,
    source_name,
):

    feed = get_feed(url)

    print(f"[{source_name}] RSS: {len(feed.entries)}件")

    new_seen = seen.copy()

    adopted_items = []

    for entry in feed.entries:

        item_url = entry.link

        if item_url in seen:
            continue

        new_seen.append(item_url)

        category = classify(entry.title)

        if category is None:
            continue

        adopted_items.append(
            {
                "title": entry.title,
                "url": item_url,
                "category": category,
            }
        )

        print(
            f"[{source_name}][{category}] {entry.title}"
        )

    print(
        f"[{source_name}] New: {len(adopted_items)}"
    )

    return adopted_items, new_seen
