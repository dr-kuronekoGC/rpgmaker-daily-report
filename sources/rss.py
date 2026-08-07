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
        タイトルとURLからカテゴリ判定する関数

    source_name:
        表示用名称

    Returns
    -------
    items, new_seen
    """

    feed = get_feed(url)

    print(
        f"[{source_name}] RSS: {len(feed.entries)}件"
    )

    new_seen = seen.copy()

    adopted_items = []

    for entry in feed.entries:

        # --------------------
        # URL取得
        # --------------------

        item_url = entry.get("link")

        if not item_url:
            continue

        # --------------------
        # 既取得チェック
        # --------------------

        if item_url in seen:
            continue

        # --------------------
        # タイトル取得
        # --------------------

        title = entry.get(
            "title",
            "タイトルなし",
        )

        # --------------------
        # 分類
        # --------------------

        try:

            result = classify(
                title,
                item_url,
            )

        except TypeError:

            result = classify(
                title,
            )

        # --------------------
        # 分類結果
        # --------------------

        if isinstance(result, tuple):

            category = result[0]
            tags = result[1]

        else:

            category = result
            tags = []

        if category is None:
            continue

        # --------------------
        # seen登録
        # --------------------

        new_seen.append(item_url)

        # --------------------
        # 採用
        # --------------------

        item = {
            "title": title,
            "url": item_url,
            "category": category,
            "source": source_name,
        }

        if tags:
            item["tags"] = tags

        adopted_items.append(item)

        print(
            f"[{source_name}][{category}] {title}"
        )

    print(
        f"[{source_name}] New: {len(adopted_items)}"
    )

    return adopted_items, new_seen
