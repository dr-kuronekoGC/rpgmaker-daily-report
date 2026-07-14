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

        if title in seen:
            continue

        new_seen.append(title)

        category = classify(title)

        if category is None:
            continue

        adopted_items.append(
            {
                "title": title,
                "url": url,
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
