"""Resource-focused collector for the Russian RPG Maker community."""

import re
import time
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from config import (
    RPGMAKER_RU_GRAPHICS_URL,
    RPGMAKER_RU_MUSIC_URL,
    RPGMAKER_RU_PLUGIN_URL,
    RPGMAKER_RU_SEEN_FILE,
)
from sources.base import get_html


SEEN_FILE = RPGMAKER_RU_SEEN_FILE
SOURCE_NAME = "RPG Maker RU"
BASE_URL = "https://rpgmaker.ru"

QUESTION_MARKERS = (
    "ищу", "помогите", "помощь", "вопрос", "как сделать",
    "как создать", "подскажите", "нужен плагин", "нужна графика",
    "нужен ресурс", "где найти", "посоветуйте", "проблема",
)


def normalize_url(url):
    if not isinstance(url, str) or not url.strip():
        return None
    absolute = urljoin(BASE_URL + "/", url.strip())
    parts = urlparse(absolute)
    if parts.netloc.lower() not in {"rpgmaker.ru", "www.rpgmaker.ru"}:
        return None
    if not re.search(r"/forum/(?:[^/]+/)*[^/]*\d{4,}[^/]*(?:/|$)", parts.path):
        return None
    return f"{BASE_URL}{parts.path}".rstrip("/")


def classify(title, category="プラグイン"):
    text = " ".join(str(title or "").lower().split())
    if not text or any(marker in text for marker in QUESTION_MARKERS):
        return None
    if any(marker in text for marker in ("правила", "регламент")):
        return None
    return category


def extract_items(html, category="プラグイン"):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    local_seen = set()
    for link in soup.select("a[href]"):
        title = link.get_text(" ", strip=True)
        url = normalize_url(link.get("href"))
        if not title or not url or url in local_seen:
            continue
        item_category = classify(title, category)
        if item_category is None:
            continue
        items.append({
            "title": title,
            "url": url,
            "category": item_category,
            "source": SOURCE_NAME,
            "language": "ru",
        })
        local_seen.add(url)
    return items


def get_items(seen):
    if not isinstance(seen, list):
        seen = []
    new_seen = list(seen)
    seen_set = set(seen)
    adopted = []
    category_pages = (
        (RPGMAKER_RU_PLUGIN_URL, "プラグイン"),
        (RPGMAKER_RU_GRAPHICS_URL, "グラフィック素材"),
        (RPGMAKER_RU_MUSIC_URL, "音楽素材"),
    )

    for index, (page_url, category) in enumerate(category_pages):
        try:
            html = get_html(page_url)
        except Exception as exc:
            print(f"[{SOURCE_NAME}] Error ({category}): {exc}")
            continue

        for item in extract_items(html, category):
            url = item["url"]
            if url in seen_set:
                continue
            seen_set.add(url)
            new_seen.append(url)
            adopted.append(item)

        if index < len(category_pages) - 1:
            time.sleep(0.5)

    if not seen:
        print(f"[{SOURCE_NAME}] Baseline: {len(new_seen)} items")
        return [], new_seen

    print(f"[{SOURCE_NAME}] New: {len(adopted)}")
    return adopted, new_seen
