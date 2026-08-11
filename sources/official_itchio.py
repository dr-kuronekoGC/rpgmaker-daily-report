# ==========================================
# itch.io Games
# ==========================================

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import (
    ITCHIO_GAME_RSS,
    ITCHIO_SEEN_FILE,
)

from sources.base import get_html


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

    for item in soup.select(
        ".game_cell"
    ):

        link = item.select_one(
            "a[href]"
        )

        if not link:
            continue

        href = link.get(
            "href"
        )

        if not href:
            continue

        href = urljoin(
            ITCHIO_GAME_RSS,
            href,
        )

        if href in seen_urls:
            continue

        seen_urls.add(href)

        if href in seen:
            continue

        # 作者ページ・一覧ページなどを除外
        if ".itch.io/" not in href:
            continue

        title_tag = item.select_one(
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

        adopted_items.append(
            {
                "title": title,
                "url": href,
                "category": "itchゲーム",
                "source": "itch.io",
            }
        )

        new_seen.append(
            href
        )

        print(
            f"[itch.io][itchゲーム] {title}"
        )

    print(
        f"[itch.io] New: "
        f"{len(adopted_items)}"
    )

    return (
        adopted_items,
        new_seen,
    )
