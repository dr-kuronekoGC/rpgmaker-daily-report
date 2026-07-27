from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import (
    OPENGAMEART_URL,
    OPENGAMEART_SEEN_FILE,
)

from categories import classify_opengameart
from sources.base import get_html


SEEN_FILE = OPENGAMEART_SEEN_FILE


def get_items(seen):

    html = get_html(OPENGAMEART_URL)

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    adopted_items = []

    new_seen = seen.copy()

    seen_urls = set()

    #
    # OpenGameArtは作品一覧のリンクを取得
    #
    for link in soup.select("a[href]"):

        href = link.get("href")

        if not href:
            continue

        #
        # artworkのみ取得
        #
        if "/content/" not in href:
            continue

        href = urljoin(
            OPENGAMEART_URL,
            href,
        )

        if href in seen_urls:
            continue

        seen_urls.add(href)

        if href in seen:
            continue

        title = link.get_text(
            " ",
            strip=True,
        )

        if len(title) < 4:
            continue

        category = classify_opengameart(title)

        if category is None:
            continue

        new_seen.append(href)

        adopted_items.append(
            {
                "title": title,
                "url": href,
                "category": category,
                "source": "OpenGameArt",
            }
        )

        print(
            f"[OpenGameArt][{category}] {title}"
        )

    print(
        f"[OpenGameArt] New: {len(adopted_items)}"
    )

    return adopted_items, new_seen
