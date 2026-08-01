from bs4 import BeautifulSoup
from config import (
    VISUSTELLA_URL,
    VISUSTELLA_SEEN_FILE,
)
from categories.asset import classify_asset
from sources.base import get_html

SEEN_FILE = VISUSTELLA_SEEN_FILE

def get_items(seen):

    html = get_html(VISUSTELLA_URL)

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    adopted_items = []

    new_seen = seen.copy()

    for link in soup.select("a[href]"):

        href = link.get("href")

        if not href:
            continue

        if "/plugins/" not in href:
            continue

        url = VISUSTELLA_URL.rstrip("/") + href

        if url in seen:
            continue

        title = link.get_text(
            " ",
            strip=True,
        )

        if not title:
            continue

        category = classify_asset(title)

        if category is None:
            continue

        adopted_items.append(
            {
                "title": title,
                "url": url,
                "category": category,
                "source": "VisuStella",
            }
        )

        new_seen.append(url)

        print(
            f"[VisuStella][{category}] {title}"
        )

    print(
        f"[VisuStella] New: {len(adopted_items)}"
    )

    return adopted_items, new_seen
