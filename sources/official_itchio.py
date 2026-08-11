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

    for link in soup.select(
        "a[href]"
    ):

        href = link.get(
            "href"
        )

        if not href:
            continue

        href = urljoin(
            ITCHIO_GAME_RSS,
            href,
        )

        # itch.ioの個別ゲームページだけ
        if ".itch.io/" not in href:
            continue

        # 一覧・タグ・ユーザー等を除外
        excluded = (
            "itch.io/games/",
            "itch.io/game-assets/",
            "itch.io/search",
            "itch.io/jam/",
            "itch.io/user/",
            "itch.io/community/",
            "itch.io/docs/",
        )

        if any(
            path in href
            for path in excluded
        ):
            continue

        if href in seen_urls:
            continue

        seen_urls.add(href)

        if href in seen:
            continue

        title = link.get_text(
            " ",
            strip=True,
        )

        if not title:
            continue

        # ナビゲーション文字列を除外
        if title.lower() in (
            "add to collection",
            "play in browser",
            "download",
        ):
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
