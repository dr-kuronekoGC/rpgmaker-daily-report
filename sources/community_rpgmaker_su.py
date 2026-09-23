import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import (
    RPGMAKER_SU_RESOURCE_URL,
    RPGMAKER_SU_PLUGIN_URL,
    RPGMAKER_SU_SEEN_FILE,
)
from sources.base import get_html


SEEN_FILE = RPGMAKER_SU_SEEN_FILE
SOURCE_NAME = "RPG Maker SU"

BASE_URL = "https://rpgmaker.su"

RESOURCE_URLS = (
    RPGMAKER_SU_RESOURCE_URL,
    RPGMAKER_SU_PLUGIN_URL,
)

MAX_PAGES_PER_SECTION = 3

QUESTION_KEYWORDS = (
    "ищу",
    "ищем",
    "нужен",
    "нужна",
    "нужно",
    "нужны",
    "помощь",
    "вопрос",
    "просьба",
    "запрос",
)

GRAPHIC_KEYWORDS = (
    "график",
    "спрайт",
    "тайл",
    "чар",
    "персонаж",
    "портрет",
    "лицо",
    "икон",
    "анимац",
    "картин",
)

SOUND_KEYWORDS = (
    "музык",
    "звук",
    "аудио",
    "bgm",
    "bgs",
    "sfx",
    "se ",
)

PLUGIN_KEYWORDS = (
    "плагин",
    "плагины",
    "plugin",
    "plugins",
    "скрипт",
    "скрипты",
    "rgss",
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

    return urljoin(BASE_URL, url).split("#", 1)[0]


def is_thread_url(url):
    if not url:
        return False

    lowered = url.lower()

    return (
        "showthread.php" in lowered
        or "/threads/" in lowered
        or re.search(r"/t\d+", lowered) is not None
    )


def classify(title, section_url):
    text = normalize_text(title)
    section = normalize_text(section_url)

    if any(keyword in text for keyword in QUESTION_KEYWORDS):
        return None

    if "f120" in section:
        return "プラグイン"

    if any(keyword in text for keyword in PLUGIN_KEYWORDS):
        return "プラグイン"

    if any(keyword in text for keyword in SOUND_KEYWORDS):
        return "サウンド素材"

    if any(keyword in text for keyword in GRAPHIC_KEYWORDS):
        return "グラフィック素材"

    # Resource section is specifically for graphics/music/sounds.
    if "f70" in section:
        return "グラフィック素材"

    return None


def extract_items(html, section_url):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    local_seen = set()

    for link in soup.select("a[href]"):
        title = link.get_text(" ", strip=True)
        url = normalize_url(link.get("href"))

        if not title or not url or not is_thread_url(url):
            continue

        if url in local_seen:
            continue

        category = classify(title, section_url)

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
    soup = BeautifulSoup(html, "html.parser")

    for link in soup.select("a[href]"):
        href = link.get("href")
        text = normalize_text(link.get_text(" ", strip=True))
        title = normalize_text(link.get("title"))

        if not href:
            continue

        if (
            text in {"next", "следующая", "вперед", "далее", "2", "3"}
            or "next" in title
            or "след" in title
        ):
            candidate = normalize_url(href)
            if candidate and candidate != current_url:
                return candidate

    return None


def get_items(seen):
    new_seen = list(seen)
    seen_set = set(seen)
    adopted_items = []

    for section_url in RESOURCE_URLS:
        current_url = section_url

        for page_number in range(1, MAX_PAGES_PER_SECTION + 1):
            try:
                html = get_html(current_url)
            except Exception as e:
                print(
                    f"[{SOURCE_NAME}] "
                    f"Page {page_number} error: {e}"
                )
                break

            page_items = extract_items(html, section_url)

            print(
                f"[{SOURCE_NAME}] "
                f"{section_url} page {page_number}: "
                f"{len(page_items)} candidate threads"
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
