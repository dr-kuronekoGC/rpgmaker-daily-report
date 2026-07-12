from bs4 import BeautifulSoup

from config import OFFICIAL_NEWS_URL
from sources.base import get_html
from categories import classify_official


def get_items(seen):

    adopted_items = []
    new_seen = seen.copy()

    try:

        html = get_html(
            OFFICIAL_NEWS_URL
        )

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        for tag in soup.find_all("h3"):

            title = tag.get_text(strip=True)

            if not title:
                continue

            if title in seen:
                continue

            new_seen.append(title)

            category = classify_official(title)

            adopted_items.append(
                {
                    "title": title,
                    "url": OFFICIAL_NEWS_URL,
                    "category": category,
                }
            )

            print(
                f"[Official][{category}] {title}"
            )

        print(
            f"[Official] New: {len(adopted_items)}"
        )

    except Exception as e:

        print(
            "[Official] Error:",
            e
        )

    return adopted_items, new_seen
