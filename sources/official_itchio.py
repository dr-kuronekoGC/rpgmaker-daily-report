# ==========================================
# itch.io Games - Debug
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

    print(
        f"[itch.io] HTML length: {len(html)}"
    )

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    links = soup.select(
        "a[href]"
    )

    print(
        f"[itch.io] Links: {len(links)}"
    )

    for link in links[:20]:

        href = link.get("href")

        title = link.get_text(
            " ",
            strip=True,
        )

        print(
            f"[itch.io][DEBUG] "
            f"{title[:80]} -> {href}"
        )

    print(
        "[itch.io] New: 0"
    )

    return [], seen
