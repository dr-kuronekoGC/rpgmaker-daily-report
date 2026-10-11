"""Collector for the Italian RPG Maker MZ plugin-release section."""

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from config import RPGMAKER_IT_MZ_PLUGIN_URL, RPGMAKER_IT_SEEN_FILE
from sources.base import get_html


SEEN_FILE = RPGMAKER_IT_SEEN_FILE
SOURCE_NAME = "Rpg2S IT"
BASE_URL = "https://www.rpg2s.it"
QUESTION_MARKERS = (
    "richiesta", "richieste", "aiuto", "supporto", "come fare",
    "problema", "problemi", "regolamento",
)


def normalize_url(url):
    if not isinstance(url, str) or not url.strip():
        return None
    absolute = urljoin(BASE_URL + "/", url.strip())
    parts = urlparse(absolute)
    if parts.netloc.lower() not in {"rpg2s.it", "www.rpg2s.it"}:
        return None
    # Invision Community stores topic paths in the query part of index.php URLs.
    candidate = absolute
    if not re.search(r"/topic/\d+", candidate):
        return None
    return candidate.split("#", 1)[0]


def classify(title):
    text = " ".join(str(title or "").lower().split())
    if not text or any(marker in text for marker in QUESTION_MARKERS):
        return None
    # The source URL is a dedicated MZ plugin release section.
    if "plugin" in text or "script" in text or "javascript" in text:
        return "Rpg2S ITプラグイン"
    # The section is for releases, so a non-question topic can still be a plugin
    # even when the title describes its feature rather than saying "plugin".
    if any(marker in text for marker in ("audio manager", "animazione", "battaglia", "finestra")):
        return "Rpg2S ITプラグイン"
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
            "language": "it",
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
        html = get_html(RPGMAKER_IT_MZ_PLUGIN_URL)
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
