import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import (
    ONIROMANCIE_SCRIPTS_URL,
    ONIROMANCIE_SEEN_FILE,
)
from sources.base import get_html


SEEN_FILE = ONIROMANCIE_SEEN_FILE
SOURCE_NAME = "Oniromancie"

BASE_URL = "https://www.rpg-maker.fr"

MAX_PAGES = 3
PAGE_SIZE = 50

PLUGIN_KEYWORDS = (
    "plugin",
    "plugins",
    "plugin mz",
    "plugin mv",
)

SCRIPT_KEYWORDS = (
    "script",
    "scripts",
    "rgss",
    "ruby",
)

QUESTION_KEYWORDS = (
    "question",
    "questions",
    "aide",
    "help",
    "recherche",
    "recherché",
    "recherch",
    "besoin",
    "demande",
    "problème",
    "probleme",
    "comment",
    "pourquoi",
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

    return urljoin(
        BASE_URL + "/",
        url,
    ).split("#", 1)[0]


def is_script_thread(title):
    text = normalize_text(title)

    if any(
        keyword in text
        for keyword in QUESTION_KEYWORDS
    ):
        return False

    return (
        any(
            keyword in text
            for keyword in PLUGIN_KEYWORDS
        )
        or any(
            keyword in text
            for keyword in SCRIPT_KEYWORDS
        )
    )


def classify(title):
    text = normalize_text(title)

    if any(
        keyword in text
        for keyword in QUESTION_KEYWORDS
    ):
        return None

    if any(
        keyword in text
        for keyword in PLUGIN_KEYWORDS
    ):
        return "プラグイン"

    if any(
        keyword in text
        for keyword in SCRIPT_KEYWORDS
    ):
        return "プラグイン"

    return None


def extract_items(html):
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    items = []
    local_seen = set()

    for link in soup.select(
        "a[href]"
    ):
        title = link.get_text(
            " ",
            strip=True,
        )

        href = link.get("href")

        if not title or not href:
            continue

        url = normalize_url(href)

        if not url or url in local_seen:
            continue

        if "index.php" not in url:
            continue

        if "id=" not in url:
            continue

        if "page=forum" not in url:
            continue

        if not is_script_thread(title):
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


def get_items(seen):
    new_seen = list(seen)
    seen_set = set(seen)
    adopted_items = []

    for page_number in range(
        MAX_PAGES
    ):
        if page_number == 0:
            page_url = ONIROMANCIE_SCRIPTS_URL
        else:
            page_url = (
                ONIROMANCIE_SCRIPTS_URL
                + f"&deb={page_number * PAGE_SIZE}"
            )

        try:
            html = get_html(page_url)
        except Exception as e:
            print(
                f"[{SOURCE_NAME}] "
                f"Page {page_number + 1} error: {e}"
            )
            break

        page_items = extract_items(html)

        print(
            f"[{SOURCE_NAME}] "
            f"Page {page_number + 1}: "
            f"{len(page_items)} script/plugin topics"
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

    if not seen:
        print(
            f"[{SOURCE_NAME}] Baseline: "
            f"{len(new_seen)} items"
        )
        return [], new_seen

    print(
        f"[{SOURCE_NAME}] New: "
        f"{len(adopted_items)}"
    )

    return adopted_items, new_seen
