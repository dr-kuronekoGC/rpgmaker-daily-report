# ==========================================
# itch.io Assets
# ==========================================

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import (
    ITCHIO_ASSET_RSS,
    ITCHIO_SEEN_FILE,
)

from sources.base import get_html

from categories.assets import classify_asset


SEEN_FILE = ITCHIO_SEEN_FILE


ITCHIO_IGNORE_TITLES = (
    "assets",
    "albums & soundtracks",
    "upload your game assets",
)


def get_items(seen):

    html = get_html(
        ITCHIO_ASSET_RSS
    )

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    print(
        f"[itch.io a] HTML length: {len(html)}"
    )

    cells = soup.select(
        ".game_cell"
    )

    print(
        f"[itch.io a] Game cells: {len(cells)}"
    )

    adopted_items = []

    new_seen = seen.copy()

    seen_urls = set()

    for cell in cells:

        title_tag = cell.select_one(
            ".game_title"
        )

        if not title_tag:
            continue

        title = title_tag.get_text(
            " ",
            strip=True,
        )

        if not title:
            continue

        if title.lower() in (
            ITCHIO_IGNORE_TITLES
        ):
            continue

        link = title_tag.find(
            "a"
        )

        if not link:
            continue

        href = link.get(
            "href"
        )

        if not href:
            continue

        href = urljoin(
            ITCHIO_ASSET_RSS,
            href,
        )

        if href in seen_urls:
            continue

        seen_urls.add(href)

        if href in seen:
            continue

        result = classify_asset(
            title,
            href,
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
            "source": "itch.io",
        }

        if tags:
            item["tags"] = tags

        adopted_items.append(
            item
        )

        new_seen.append(
            href
        )

        print(
            f"[itch.io a][{category}] {title}"
        )

    print(
        f"[itch.io a] New: "
        f"{len(adopted_items)}"
    )

    return (
        adopted_items,
        new_seen,
    )
