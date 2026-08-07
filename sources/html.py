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

        if href_filter:

            if not href_filter(href):
                continue

        if href in seen_urls:
            continue

        seen_urls.add(href)

        if href in seen:
            continue

        title = tag.get_text(
            " ",
            strip=True,
        )

        if not title:
            continue


        try:

            result = classify(
                title,
                href,
            )

        except TypeError:

            result = classify(
                title,
            )


        if isinstance(result, tuple):

            category = result[0]
            tags = result[1]

        else:

            category = result
            tags = []


        if category is None:
            continue


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
