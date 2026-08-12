# ==========================================
# itch.io Assets
# ==========================================

import requests

from bs4 import BeautifulSoup

from config import (
    ITCHIO_ASSET_RSS,
    ITCHIO_SEEN_FILE,
    REQUEST_TIMEOUT,
)

from sources.base import HEADERS

from categories.assets import classify_asset


SEEN_FILE = ITCHIO_SEEN_FILE


ITCHIO_IGNORE_TITLES = (
    "assets",
    "albums & soundtracks",
    "upload your game assets",
)


def get_items(seen):

    response = requests.get(
        ITCHIO_ASSET_RSS,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    html = response.content.decode(
        "utf-8",
        errors="replace",
    )

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    adopted_items = []

    new_seen = seen.copy()

    seen_urls = set()

    for cell in soup.select(
        ".game_cell"
    ):

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

        if href.startswith("/"):
            href = (
                "https://itch.io"
                + href
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
