from config import (
    FORUM_URL,
    FORUM_SEEN_FILE,
)

from bs4 import BeautifulSoup

from categories import classify_forum
from sources.html import get_html


SEEN_FILE = FORUM_SEEN_FILE


def get_items(seen):

    adopted_items = []

    new_seen = seen.copy()

    try:

        html = get_html(
            FORUM_URL
        )

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        for tag in soup.select("h3, h4"):

            title = tag.get_text(strip=True)

            if not title:
                continue

            if title in seen:
                continue

            category = classify_forum(title)

            if category is None:
                continue

            new_seen.append(title)

            adopted_items.append(
                {
                    "title": title,
                    "url": FORUM_URL,
                    "category": category,
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
