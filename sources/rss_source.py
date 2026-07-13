import feedparser


def collect_rss_items(
    rss_url,
    seen,
    classifier,
    source_name,
):

    feed = feedparser.parse(rss_url)

    print(
        f"[{source_name}] RSS: {len(feed.entries)}件"
    )

    adopted_items = []

    new_seen = seen.copy()

    for entry in feed.entries:

        url = entry.link

        if url in seen:
            continue

        new_seen.append(url)

        category = classifier(entry.title)

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
            f"[{source_name}][{category}] {entry.title}"
        )

    print(
        f"[{source_name}] New: {len(adopted_items)}"
    )

    return adopted_items, new_seen
