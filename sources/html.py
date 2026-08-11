from urllib.parse import urljoin

from bs4 import BeautifulSoup

from sources.base import get_html


def collect_html(
    *,
    url,
    seen,
    classify,
    selector,
    source_name,
    href_filter=None,
):

    html = get_html(url)

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    adopted_items = []

    new_seen = seen.copy()

    seen_urls = set()

    for tag in soup.select(selector):

        href = None

        # ----------------------------
        # URL取得
        # ----------------------------

        if tag.name == "a":

            href = tag.get("href")

        else:

            link = tag.find("a")

            if link:
                href = link.get("href")

        if not href:
            continue

        href = urljoin(
            url,
            href,
        )

        # ----------------------------
        # URLフィルター
        # ----------------------------

        if href_filter:

            if not href_filter(href):
                continue

        # ----------------------------
        # 重複URL除外
        # ----------------------------

        if href in seen_urls:
            continue

        seen_urls.add(href)

        if href in seen:
            continue

        # ----------------------------
        # タイトル取得
        # ----------------------------

        title = tag.get_text(
            " ",
            strip=True,
        )

        if not title:
            continue

        # ----------------------------
        # ナビゲーション等の
        # 異常に長いテキストを除外
        # ----------------------------

        if len(title) > 300:
            continue

        # ----------------------------
        # 分類
        # ----------------------------

        try:

            result = classify(
                title,
                href,
            )

        except TypeError:

            result = classify(
                title,
            )

        # ----------------------------
        # 分類結果
        # ----------------------------

        if isinstance(result, tuple):

            category = result[0]
            tags = result[1]

        else:

            category = result
            tags = []

        if category is None:
            continue

        # ----------------------------
        # 採用
        # ----------------------------

        item = {
            "title": title,
            "url": href,
            "category": category,
            "source": source_name,
        }

        if tags:
            item["tags"] = tags

        adopted_items.append(item)

        new_seen.append(href)

        print(
            f"[{source_name}][{category}] {title}"
        )

    print(
        f"[{source_name}] New: {len(adopted_items)}"
    )

    return adopted_items, new_seen
