# ==========================================
# itch.io Games
# ==========================================

from config import (
    ITCHIO_GAME_RSS,
    ITCHIO_SEEN_FILE,
)

from sources.base import get_html

from bs4 import BeautifulSoup


SEEN_FILE = ITCHIO_SEEN_FILE


def get_items(seen):

    html = get_html(
        ITCHIO_GAME_RSS
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

        link = title_tag.find(
            "a"
        )

        if not link:
            link = cell.select_one(
                "a[href]"
            )

        if not link:
            continue

        href = link.get(
            "href"
        )

        if not href:
            continue

        if href.startswith(
            "/"
        ):
            href = (
                "https://itch.io"
                + href
            )

        if href in seen_urls:
            continue

        seen_urls.add(href)

        if href in seen:
            continue

        item = {
            "title": title,
            "url": href,
            "category": "itchゲーム",
            "source": "itch.io",
        }

        adopted_items.append(
            item
        )

        new_seen.append(
            href
        )

        print(
            f"[itch.io g][itchゲーム] "
            f"{title}"
        )

    print(
        f"[itch.io g] New: "
        f"{len(adopted_items)}"
    )

    return (
        adopted_items,
        new_seen,
    )
