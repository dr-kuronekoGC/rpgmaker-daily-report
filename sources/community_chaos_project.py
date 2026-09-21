import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import (
    CHAOS_PROJECT_RESOURCE_URL,
    CHAOS_PROJECT_SEEN_FILE,
)
from sources.base import get_html

SEEN_FILE = CHAOS_PROJECT_SEEN_FILE
SOURCE_NAME = "Chaos Project"

BASE_URL = "https://forum.chaos-project.com"

MAX_PAGES = 5

SOUND_KEYWORDS = (
    "sound",
    "audio",
    "bgm",
    "bgs",
    "music",
    "sfx",
    "sound effect",
    "sound effects",
)

PLUGIN_KEYWORDS = (
    "plugin",
    "plugins",
    "script",
    "scripts",
    "rgss",
)

GRAPHIC_KEYWORDS = (
    "tileset",
    "tilesets",
    "sprite",
    "sprites",
    "chara",
    "character",
    "characters",
    "face",
    "faceset",
    "facesets",
    "battler",
    "battlers",
    "icon",
    "icons",
    "graphic",
    "graphics",
    "pixel",
    "pixelart",
    "animation",
    "animations",
    "resource",
    "resources",
)

QUESTION_KEYWORDS = (
    "request",
    "requests",
    "question",
    "help",
    "looking for",
    "need ",
)


def normalize_text(value):
    if not isinstance(value, str):
        return ""
    return " ".join(value.lower().split())


def normalize_url(url):
    if not isinstance(url, str):
        return None

    url = url.strip()

    if not url:
        return None

    if url.startswith("/"):
        url = urljoin(BASE_URL, url)

    url = url.split("#", 1)[0]

    # SMF may use either topic=123.0 or topic,123.0.html.
    match = re.search(r"topic[=,](\d+)", url)
    if match:
        return urljoin(
            BASE_URL,
            f"/index.php?topic={match.group(1)}.0",
        )

    return url


def classify(title):
    text = normalize_text(title)

    if any(
        keyword in text
        for keyword in QUESTION_KEYWORDS
    ):
        return None

    if any(
        keyword in text
        for keyword in SOUND_KEYWORDS
    ):
        return "サウンド素材"

    if any(
        keyword in text
        for keyword in PLUGIN_KEYWORDS
    ):
        return "プラグイン"

    if any(
        keyword in text
        for keyword in GRAPHIC_KEYWORDS
    ):
        return "グラフィック素材"

    # Resource Database is already a resource-focused board.
    # Titles without a more specific keyword are still useful
    # as material information, so classify them as graphics by default.
    return "グラフィック素材"


def extract_items(html):
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    items = []
    local_seen = set()

    selectors = [
        "td.subject a[href*='topic=']",
        "span.subject a[href*='topic=']",
        "a[href*='topic=']",
        "a[href*='topic,']",
    ]

    links = []

    for selector in selectors:
        links = soup.select(selector)
        if links:
            break

    for link in links:
        title = link.get_text(
            " ",
            strip=True,
        )

        url = normalize_url(
            link.get("href")
        )

        if not title or not url:
            continue

        if url in local_seen:
            continue

        category = classify(title)

        if category is None:
            continue

        items.append(
            {
                "title": title,
                "url": url,
                "category": category,
                "source": SOURCE_NAME,
            }
        )

        local_seen.add(url)

    return items


def get_next_page_url(html, current_url):
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    selectors = [
        "a.navPages[href]",
        "a[href*='board=17.']",
        "a[href*='board%3D17.']",
    ]

    for link in soup.select(
        ", ".join(selectors)
    ):
        href = link.get("href")
        text = link.get_text(
            " ",
            strip=True,
        ).lower()

        if not href:
            continue

        if text in {"next", "go down"} or "next" in text:
            return urljoin(
                current_url,
                href,
            )

    # SMF pagination links can also be identified by a title.
    for link in soup.select("a[href]"):
        title = (
            link.get("title")
            or ""
        ).lower()

        if "next" in title:
            return urljoin(
                current_url,
                link.get("href"),
            )

    return None


def get_items(seen):
    new_seen = list(seen)
    seen_set = set(seen)
    adopted_items = []

    current_url = CHAOS_PROJECT_RESOURCE_URL

    for page_number in range(
        1,
        MAX_PAGES + 1,
    ):
        try:
            html = get_html(
                current_url
            )
        except Exception as e:
            print(
                f"[{SOURCE_NAME}] "
                f"Page {page_number} error: {e}"
            )
            break

        page_items = extract_items(html)

        print(
            f"[{SOURCE_NAME}] "
            f"Page {page_number}: "
            f"{len(page_items)} resource topics"
        )

        for item in page_items:
            url = item["url"]

            if url in seen_set:
                continue

            new_seen.append(url)
            seen_set.add(url)
            adopted_items.append(item)

            print(
                f"[{SOURCE_NAME}]"
                f"[{item['category']}] "
                f"{item['title']}"
            )

        next_url = get_next_page_url(
            html,
            current_url,
        )

        if not next_url or next_url == current_url:
            break

        current_url = next_url

    print(
        f"[{SOURCE_NAME}] New: "
        f"{len(adopted_items)}"
    )

    return adopted_items, new_seen
