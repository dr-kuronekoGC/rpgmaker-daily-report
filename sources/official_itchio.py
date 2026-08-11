# ==========================================
# itch.io Games
# ==========================================

from config import (
    ITCHIO_GAME_RSS,
    ITCHIO_SEEN_FILE,
)

from sources.html import collect_html


SEEN_FILE = ITCHIO_SEEN_FILE


def is_itchio_game(url):

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
        path in url
        for path in excluded
    ):
        return False

    return (
        ".itch.io/" in url
        and url.rstrip("/") != ITCHIO_GAME_RSS.rstrip("/")
    )


def classify_itch_game(
    title,
    url="",
):

    if not title:
        return None

    return "itchゲーム"


def get_items(seen):

    try:

        return collect_html(
            url=ITCHIO_GAME_RSS,
            seen=seen,
            classify=classify_itch_game,
            selector="a",
            source_name="itch.io",
            href_filter=is_itchio_game,
        )

    except Exception as e:

        print(
            f"[itch.io] Skip: {e}"
        )

        return [], seen
