from urllib.parse import urljoin

from bs4 import BeautifulSoup

from sources.base import get_html


def collect_html(

    url,
    seen,
    classify,
    source_name,

    link_selector="a[href]",

    title_selector=None,

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

    for link in soup.select(link_selector):

        href = link.get("href")

        if not href:
            continue

        href = urljoin(
            url,
            href,
        )

        if href_filter:

            if not href_filter(href):
                continue

        if href in seen_urls:
            continue

        seen_urls.add(href)

        if href in seen:
            continue

        if title_selector:

            title_node = link.select_one(title_selector)

            if title_node:

                title = title_node.get_text(
                    " ",
                    strip=True,
                )

            else:

                title = link.get_text(
                    " ",
                    strip=True,
                )

        else:

            title = link.get_text(
                " ",
                strip=True,
            )

        if not title:
            continue

        category = classify(title)

        if category is None:
            continue

        adopted_items.append(
            {
                "title": title,
                "url": href,
                "category": category,
                "source": source_name,
            }
        )

        new_seen.append(href)

        print(
            f"[{source_name}][{category}] {title}"
        )

    print(
        f"[{source_name}] New: {len(adopted_items)}"
    )

    return adopted_items, new_seen
