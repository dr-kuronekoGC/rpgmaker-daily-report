# ==========================================
# itch.io Games
# ==========================================

from config import (
    ITCHIO_GAME_RSS,
    ITCHIO_SEEN_FILE,
)

from sources.html import collect_html

from categories.itch import classify_itch


SEEN_FILE = ITCHIO_SEEN_FILE


def is_itchio_game(url):

    return True


def get_items(seen):

    try:

        return collect_html(
            url=ITCHIO_GAME_RSS,
            seen=seen,
            classify=classify_itch,
            selector="a",
            source_name="itch.io",
            href_filter=is_itchio_game,
        )

    except Exception as e:

        print(
            f"[itch.io] Skip: {e}"
        )

        return [], seen
