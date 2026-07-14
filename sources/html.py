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

    for tag in soup.select(selector):

        title = tag.get_text(strip=True)

        if not title:
            continue

        category = classify(title)

        if category is None:
            continue

        # --------------------
        # URL取得
        # --------------------

        href = None

        link = tag.find("a")

        if link:

            href = link.get("href")

        if not href:

            href = url

        elif href.startswith("/"):

            href = url.rstrip("/") + href

        # --------------------

        if href in seen:
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
