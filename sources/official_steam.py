from bs4 import BeautifulSoup

from config import (
    OFFICIAL_STEAM_URL,
    OFFICIAL_STEAM_SEEN_FILE,
)

from categories import classify_steam

from sources.base import get_html


SEEN_FILE = OFFICIAL_STEAM_SEEN_FILE


def get_items(seen):

    adopted_items = []

    new_seen = seen.copy()

    try:

        html = get_html(
            OFFICIAL_STEAM_URL
        )

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        for link in soup.select("a.apphub_Card"):

            title_tag = link.select_one(
                ".apphub_CardContentTitle"
            )

            if title_tag is None:
                continue

            title = title_tag.get_text(
                strip=True
            )

            if len(title) < 10:
                continue

            if title in seen:
                continue

            url = link.get("href")

            if not url:
                continue

            if "/news/" not in url:
                continue

            category = classify_steam(title)

            adopted_items.append(
                {
                    "title": title,
                    "url": url,
                    "category": category,
                    "source": "Steam",
                }
            )

            new_seen.append(title)

            print(
                f"[Steam][{category}] {title}"
            )

        print(
            f"[Steam] New: {len(adopted_items)}"
        )

    except Exception as e:

        print(
            "[Steam] Error:",
            e,
        )

    return adopted_items, new_seen
