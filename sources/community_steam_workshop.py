"""Collect resource-tagged items from the RPG Maker MZ Steam Workshop."""

from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup

from config import STEAM_WORKSHOP_QUERIES, STEAM_WORKSHOP_SEEN_FILE
from sources.base import get_html


SEEN_FILE = STEAM_WORKSHOP_SEEN_FILE
SOURCE_NAME = "Steam Workshop RPG Maker MZ"
BASE_URL = "https://steamcommunity.com"


def normalize_url(url):
    if not isinstance(url, str) or not url.strip():
        return None
    absolute = urljoin(BASE_URL + "/", url.strip())
    parts = urlparse(absolute)
    if parts.netloc.lower() not in {"steamcommunity.com", "www.steamcommunity.com"}:
        return None
    if not parts.path.startswith("/sharedfiles/filedetails/"):
        return None
    item_id = parse_qs(parts.query).get("id", [None])[0]
    if not item_id or not item_id.isdigit():
        return None
    return f"{BASE_URL}/sharedfiles/filedetails/?id={item_id}"


def extract_items(html, category):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    local_seen = set()

    for link in soup.select('a[href*="/sharedfiles/filedetails/"]'):
        url = normalize_url(link.get("href"))
        if not url or url in local_seen:
            continue

        title_tag = link.select_one(".workshopItemTitle")
        title = title_tag.get_text(" ", strip=True) if title_tag else ""
        if not title:
            title = link.get("title", "").strip()
        if not title or title.lower() in {"view all", "browse", "next", "previous"}:
            continue

        items.append({
            "title": title,
            "url": url,
            "category": category,
            "source": SOURCE_NAME,
            "language": "多言語",
        })
        local_seen.add(url)

    return items


def get_items(seen):
    if not isinstance(seen, list):
        seen = []

    new_seen = list(seen)
    seen_set = set(seen)
    adopted = []
    failed = 0

    for category, url in STEAM_WORKSHOP_QUERIES:
        try:
            html = get_html(url)
        except Exception as exc:
            failed += 1
            print(f"[{SOURCE_NAME}] Error ({category}): {exc}")
            continue

        for item in extract_items(html, category):
            item_url = item["url"]
            if item_url in seen_set:
                continue
            seen_set.add(item_url)
            new_seen.append(item_url)
            adopted.append(item)

    if not seen:
        print(f"[{SOURCE_NAME}] Baseline: {len(new_seen)} items; failed queries={failed}")
        return [], new_seen

    print(f"[{SOURCE_NAME}] New: {len(adopted)}; failed queries={failed}")
    return adopted, new_seen
