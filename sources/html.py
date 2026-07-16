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

        # --------------------
        # URL取得
        # --------------------

        href = None

        if tag.name == "a":

            href = tag.get("href")

        else:

            link = tag.find("a")

            if link:
                href = link.get("href")

        if not href:
            continue

        href = urljoin(url, href)

        # --------------------
        # 重複除去
        # --------------------

        if href in seen_urls:
            continue

        seen_urls.add(href)

        if href in seen:
            continue

        # --------------------
        # タイトル取得
        # --------------------

        title = tag.get_text(
            " ",
            strip=True,
        )

        if not title:
            continue

        category = classify(title)

        if category is None:
            continue

        new_seen.append(href)

        adopted_items.append(
            {
                "title": title,
                "url": href,
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
