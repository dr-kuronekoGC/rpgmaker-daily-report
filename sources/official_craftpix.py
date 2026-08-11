# ==========================================
# CraftPix
# ==========================================

from config import (
    CRAFTPIX_RSS,
    CRAFTPIX_SEEN_FILE,
)

from sources.html import collect_html

from categories.assets import classify_asset


SEEN_FILE = CRAFTPIX_SEEN_FILE


CRAFTPIX_IGNORE_TITLES = (
    "sprites & characters",
    "characters & sprites",
    "gui",
    "backgrounds",
    "icons",
    "tilesets",
    "cart",
    "3d game assets",
    "pixel art sprites",
    "platformer tilesets",
    "defense game asset kits",
    "top-down tilesets",
    "pixel art icons",
    "pixel art tilesets",
    "fantasy avatar icons",
    "cartoon sprites",
    "top-down sprites",
)


def is_craftpix_item(url):

    excluded = (
        "/category/",
        "/tag/",
        "/author/",
        "/page/",
        "/freebies/",
        "/blog/",
        "/about/",
        "/contact/",
    )

    if any(
        path in url
        for path in excluded
    ):
        return False

    return (
        "craftpix.net/" in url
        and url.rstrip("/") != CRAFTPIX_RSS.rstrip("/")
    )


def classify_craftpix(
    title,
    url="",
):

    normalized = title.lower().strip()

    if normalized in CRAFTPIX_IGNORE_TITLES:
        return None

    return classify_asset(
        title,
        url,
    )


def get_items(seen):

    try:

        return collect_html(
            url=CRAFTPIX_RSS,
            seen=seen,
            classify=classify_craftpix,
            selector="a",
            source_name="CraftPix",
            href_filter=is_craftpix_item,
        )

    except Exception as e:

        print(
            f"[CraftPix] Skip: {e}"
        )

        return [], seen
