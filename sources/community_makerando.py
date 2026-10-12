"""Collect clearly resource-related topics from the Makerando forum."""

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from config import MAKERANDO_FORUM_URL, MAKERANDO_SEEN_FILE
from sources.base import get_html

SEEN_FILE = MAKERANDO_SEEN_FILE
SOURCE_NAME = "Makerando IT"
BASE_URL = "https://www.makerando.com"

GRAPHIC_KEYWORDS = (
    "risorsa", "risorse", "grafica", "grafiche", "charset", "charaset",
    "faceset", "chipset", "tileset", "battleback", "battler", "sprite",
    "pixel art", "animazione", "animazioni", "icone", "icone mz",
)
SOUND_KEYWORDS = (
    "audio", "musica", "musiche", "suono", "suoni", "sound", "bgm",
    "bgs", "sfx", "effetti sonori",
)
PLUGIN_KEYWORDS = (
    "plugin", "plugins", "script", "scripts", "javascript", "rgss",
    "patch", "utility", "utilità", "utilita", "tool",
)
QUESTION_KEYWORDS = (
    "richiesta", "richieste", "aiuto", "supporto", "come fare",
    "problema", "problemi", "cerco", "cerchiamo", "qualcuno sa",
)


def normalize_url(url):
    if not isinstance(url, str) or not url.strip():
        return None
    absolute = urljoin(BASE_URL + "/", url.strip())
    parts = urlparse(absolute)
    if parts.netloc.lower() not in {"makerando.com", "www.makerando.com"}:
        return None
    if not re.search(r"/(?:forum/)?topic/\d+", parts.path):
        return None
    return absolute.split("#", 1)[0].split("?", 1)[0]


def classify(title, context=""):
    title_text = " ".join(str(title or "").lower().split())
    text = " ".join(f"{title_text} {context}".lower().split())
    if not title_text or any(word in title_text for word in QUESTION_KEYWORDS):
        return None
    if any(word in text for word in PLUGIN_KEYWORDS):
        return "Makerando ITプラグイン"
    if any(word in text for word in SOUND_KEYWORDS):
        return "Makerando ITサウンド素材"
    if any(word in text for word in GRAPHIC_KEYWORDS):
        return "Makerando ITグラフィック素材"
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

        parent = link.parent
        context = parent.get_text(" ", strip=True) if parent else ""
        category = classify(title, context)
        if category is None:
            continue

        items.append({
            "title": title,
            "url": url,
            "category": category,
            "source": SOURCE_NAME,
            "language": "it",
        })
        local_seen.add(url)

    return items


def get_items(seen):
    if not isinstance(seen, list):
        seen = []

    try:
        html = get_html(MAKERANDO_FORUM_URL)
    except Exception as exc:
        print(f"[{SOURCE_NAME}] Error: {exc}")
        return [], seen

    items = extract_items(html)
    new_seen = list(seen)
    seen_set = set(seen)
    adopted = []

    for item in items:
        url = item["url"]
        if url in seen_set:
            continue
        new_seen.append(url)
        seen_set.add(url)
        adopted.append(item)

    if not seen:
        print(f"[{SOURCE_NAME}] Baseline: {len(new_seen)} topic URLs")
        return [], new_seen

    print(f"[{SOURCE_NAME}] New resource topics: {len(adopted)}")
    return adopted, new_seen
