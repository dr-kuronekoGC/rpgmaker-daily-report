"""Conservative collector for the Russian RPG Maker plugin section."""

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from config import RPGMAKER_RU_PLUGIN_URL, RPGMAKER_RU_SEEN_FILE
from sources.base import get_html


SEEN_FILE = RPGMAKER_RU_SEEN_FILE
SOURCE_NAME = "RPG Maker RU"
BASE_URL = "https://rpgmaker.ru"
MAX_PAGES = 1

QUESTION_MARKERS = (
    "ищу", "помогите", "помощь", "вопрос", "как сделать",
    "как создать", "подскажите", "нужен плагин",
)


def normalize_url(url):
    if not isinstance(url, str) or not url.strip():
        return None
    absolute = urljoin(BASE_URL + "/", url.strip())
    parts = urlparse(absolute)
    if parts.netloc.lower() not in {"rpgmaker.ru", "www.rpgmaker.ru"}:
        return None
    if not re.search(r"/forum/[^/]*\d{4,}[^/]*(?:/|$)", parts.path):
        return None
    return f"{BASE_URL}{parts.path}".rstrip("/")


def classify(title):
    text = " ".join(str(title or "").lower().split())
    if not text or any(marker in text for marker in QUESTION_MARKERS):
        return None
    # The configured page is a dedicated MZ plugin/resource section.
    # Avoid pulling generic help posts just because they mention a plugin.
    if any(marker in text for marker in ("плагин", "плагины", "plugin", "скрипт", "скрипты")):
        return "RPG Maker RUプラグイン"
    if any(marker in text for marker in ("музык", "звук", "саунд", "bgm", "bgs", "se")):
        return "RPG Maker RUサウンド素材"
    if any(marker in text for marker in ("график", "ресурс", "тайлсет", "спрайт", "иконк")):
        return "RPG Maker RUグラフィック素材"
    if any(marker in text for marker in ("урок", "гайд", "инструкц", "совет")):
        return "RPG Maker RU Tips"
    return None


def extract_items(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    local_seen = set()
    for link in soup.select("a[href]"):
        title = link.get_text(" ", strip=True)
        url = normalize_url(link.get("href"))
        if not title or not url or url in local_seen:
            continue
        category = classify(title)
        if category is None:
            continue
        items.append({
            "title": title,
            "url": url,
            "category": category,
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
    try:
        html = get_html(RPGMAKER_RU_PLUGIN_URL)
    except Exception as exc:
        print(f"[{SOURCE_NAME}] Error: {exc}")
        return [], seen

    for item in extract_items(html):
        url = item["url"]
        if url in seen_set:
            continue
        seen_set.add(url)
        new_seen.append(url)
        adopted.append(item)

    if not seen:
        print(f"[{SOURCE_NAME}] Baseline: {len(new_seen)} items")
        return [], new_seen
    print(f"[{SOURCE_NAME}] New: {len(adopted)}")
    return adopted, new_seen
