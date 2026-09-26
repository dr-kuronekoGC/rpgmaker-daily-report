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
SOURCE_NAME = "Нейтральная полоса"

BASE_URL = "https://rpgmaker.su"

RESOURCE_URLS = (
    (RPGMAKER_SU_RESOURCE_URL, "resource"),
    (RPGMAKER_SU_PLUGIN_URL, "plugin"),
)

MAX_PAGES_PER_SECTION = 3

QUESTION_KEYWORDS = (
    "ищу",
    "ищем",
    "нужен",
    "нужна",
    "нужно",
    "нужны",
    "поиск",
    "помощь",
    "вопрос",
    "просьба",
    "запрос",
    "как ",
    "подскаж",
)

IGNORE_KEYWORDS = (
    "руссификац",
    "перевод",
    "программа для перевода",
)

SOUND_KEYWORDS = (
    "музык",
    "музыка",
    "звук",
    "звуки",
    "аудио",
    "bgm",
    "bgs",
    "sfx",
    "se ",
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
    "ресурс",
    "ресурсы",
    "dlc",
)

THREAD_PATTERN = re.compile(
    r"/f(?:70|109)/[^/?]+-\d+/?$",
    re.IGNORECASE,
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

    url = urljoin(BASE_URL, url)
    url = url.split("#", 1)[0]
    url = url.split("?", 1)[0]

    return url


def is_thread_url(url):
    if not url:
        return False

    return THREAD_PATTERN.search(url) is not None


def classify(title, section_type):
    text = normalize_text(title)

    if any(
        keyword in text
        for keyword in QUESTION_KEYWORDS
    ):
        return None

    if any(
        keyword in text
        for keyword in IGNORE_KEYWORDS
    ):
        return None

    if section_type == "plugin":
        return "プラグイン"

    if any(
        keyword in text
        for keyword in SOUND_KEYWORDS
    ):
        return "サウンド素材"

    if any(
        keyword in text
        for keyword in GRAPHIC_KEYWORDS
    ):
        return "グラフィック素材"

    # Resource section is explicitly for graphics/music/sounds.
    # Default to graphics when the title is not otherwise identifiable.
    if section_type == "resource":
        return "グラフィック素材"

    return None


def extract_items(html, section_type):
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    items = []
    local_seen = set()

    for link in soup.select("a[href]"):
        title = link.get_text(
            " ",
            strip=True,
        )
        url = normalize_url(
            link.get("href")
        )

        if not title or not url:
            continue

        if not is_thread_url(url):
            continue

        if url in local_seen:
            continue

        category = classify(
            title,
            section_type,
        )

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


def get_page_url(section_url, page_number):
    if page_number <= 1:
        return section_url

    return section_url.rstrip("/") + (
        f"/index{page_number}"
    )


def get_items(seen):
    new_seen = list(seen)
    seen_set = set(seen)
    adopted_items = []

    for section_url, section_type in RESOURCE_URLS:
        for page_number in range(
            1,
            MAX_PAGES_PER_SECTION + 1,
        ):
            current_url = get_page_url(
                section_url,
                page_number,
            )

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

            page_items = extract_items(
                html,
                section_type,
            )

            print(
                f"[{SOURCE_NAME}] "
                f"{section_type} "
                f"page {page_number}: "
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
