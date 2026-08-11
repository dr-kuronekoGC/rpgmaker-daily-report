# ==========================================
# itch.io Games - Debug 2
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

    print(
        f"[itch.io] HTML length: {len(html)}"
    )

    # ゲームカード候補を確認
    selectors = (
        ".game_cell",
        ".game_link",
        ".game_title",
        ".game_grid_widget",
        ".game_thumb",
    )

    for selector in selectors:

        elements = soup.select(
            selector
        )

        print(
            f"[itch.io] "
            f"{selector}: "
            f"{len(elements)}"
        )

        for element in elements[:5]:

            print(
                f"[itch.io][DEBUG] "
                f"{element.get_text(' ', strip=True)[:100]}"
            )

    print(
        "[itch.io] New: 0"
    )

    return [], seen
