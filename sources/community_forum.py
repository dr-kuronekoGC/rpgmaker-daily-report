from bs4 import BeautifulSoup

from config import (
    FORUM_URL,
    FORUM_SEEN_FILE,
)

from categories import classify_forum
from sources.html import get_html


SEEN_FILE = FORUM_SEEN_FILE


def get_items(seen):

    adopted_items = []

    new_seen = seen.copy()

    try:

        html = get_html(FORUM_URL)

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        seen_titles = set()

        for link in soup.select("a"):

            title = link.get_text(strip=True)

            if not title:
                continue

            if len(title) < 8:
                continue

            if title in seen_titles:
                continue

            seen_titles.add(title)

            if url in seen:
                continue

            category = classify_forum(title)

            if category is None:
                continue

            url = link.get("href")

            if not url:
                continue

            if url.startswith("/"):
                url = (
                    "https://forums.rpgmakerweb.com"
                    + url
                )

            if "/threads/" not in url:
                continue

            new_seen.append(url)

            adopted_items.append(
                {
                    "title": title,
                    "url": url,
                    "category": category,
                    "source": "Forum",
                }
            )

            print(
                f"[Forum][{category}] {title}"
            )

        print(
            f"[Forum] New: {len(adopted_items)}"
        )

    except Exception as e:

        print(
            "[Forum] Error:",
            e,
        )

    return adopted_items, new_seen
