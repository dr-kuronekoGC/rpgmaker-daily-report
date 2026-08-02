from sources.base import get_feed


def collect_rss(
    *,
    url,
    seen,
    classify,
    source_name,
):
    """
    RSS共通取得処理

    Parameters
    ----------
    url:
        RSS URL
    seen:
        過去取得済みURL一覧
    classify:
        タイトルからカテゴリ判定する関数
    source_name:
        表示用名称

    Returns
    -------
    items, new_seen
    """

    feed = get_feed(url)

    print(f"[{source_name}] RSS: {len(feed.entries)}件")

    new_seen = seen.copy()

    adopted_items = []

    for entry in feed.entries:

        item_url = entry.get("link")

        if not item_url:
            continue

        if item_url in seen:
            continue

        new_seen.append(item_url)

        title = entry.get(
            "title",
            "タイトルなし"
        )

        category = classify(title)

        if category is None:
            continue

        adopted_items.append(
            {
                "title": title,
                "url": item_url,
                "category": category,
            }
        )

        print(
            f"[{source_name}][{category}] {title}"
        )

    print(
        f"[{source_name}] New: {len(adopted_items)}"
    )

    return adopted_items, new_seen
