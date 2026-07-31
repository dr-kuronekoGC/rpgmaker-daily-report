from bs4 import BeautifulSoup

from config import (
    GAMEDEVMARKET_URL,
    GAMEDEVMARKET_SEEN_FILE,
)

from categories import classify_gamedevmarket

from sources.base import get_html


SEEN_FILE = GAMEDEVMARKET_SEEN_FILE


def get_items(seen):

    adopted_items = []

    new_seen = seen.copy()

    try:

        html = get_html(
            GAMEDEVMARKET_URL
        )

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        seen_urls = set()

        for link in soup.select("a[href]"):

            href = link.get("href")

            if not href:
                continue

            if "/product/" not in href:
                continue

            if href in seen_urls:
                continue

            seen_urls.add(href)

            if href in seen:
                continue

            title = link.get_text(
                strip=True
            )

            if not title:
                continue

            category = classify_gamedevmarket(
                title
            )

            if category is None:
                continue

            adopted_items.append(
                {
                    "title": title,
                    "url": href,
                    "category": category,
                    "source": "GameDevMarket",
                }
            )

            new_seen.append(href)

            print(
                f"[GameDevMarket][{category}] {title}"
            )

        print(
            f"[GameDevMarket] New: {len(adopted_items)}"
        )

    except Exception as e:

        print(
            "[GameDevMarket] Error:",
            e,
        )

    return adopted_items, new_seen
