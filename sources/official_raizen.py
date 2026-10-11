# ==========================================
# Raizen's RPG Maker Plugins
# ==========================================

from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from config import (
    RAIZEN_PLUGINS_URL,
    RAIZEN_PLUGINS_SEEN_FILE,
)
from sources.base import get_html


SEEN_FILE = RAIZEN_PLUGINS_SEEN_FILE
SOURCE_NAME = "Raizen's Plugins"
ITEM_CATEGORY = "Raizenプラグイン"


def normalize_product_url(url):
    if not isinstance(url, str) or not url.strip():
        return None

    absolute = urljoin(RAIZEN_PLUGINS_URL, url.strip())
    parts = urlsplit(absolute)

    if parts.netloc.lower() != "raizen884.itch.io":
        return None

    if parts.path in {"", "/"}:
        return None

    return urlunsplit((
        "https",
        "raizen884.itch.io",
        parts.path.rstrip("/"),
        "",
        "",
    ))


def extract_products(html, seen_urls=None):
    """Extract unique product cards from Raizen's itch.io creator page."""
    seen_urls = set(seen_urls or [])
    soup = BeautifulSoup(html, "html.parser")
    items = []
    found_urls = set()

    for cell in soup.select(".game_cell"):
        link = cell.select_one("a[href]")
        if not link:
            continue

        url = normalize_product_url(link.get("href"))
        if not url or url in seen_urls or url in found_urls:
            continue

        title_tag = cell.select_one(".game_title")
        title = (
            title_tag.get_text(" ", strip=True)
            if title_tag
            else link.get_text(" ", strip=True)
        )
        title = " ".join(title.split()).strip()

        if not title:
            continue

        found_urls.add(url)
        items.append({
            "title": title,
            "url": url,
            "category": ITEM_CATEGORY,
            "source": SOURCE_NAME,
        })

    return items


def get_items(seen):
    """Track new products without publishing the existing catalogue on first run."""
    if not isinstance(seen, list):
        seen = []

    try:
        html = get_html(RAIZEN_PLUGINS_URL)
        current_items = extract_products(html)
        current_urls = [item["url"] for item in current_items]

        if not seen:
            print(
                f"[{SOURCE_NAME}] Baseline: {len(current_urls)} products"
            )
            return [], current_urls

        seen_set = set(seen)
        new_seen = list(seen)
        adopted_items = []

        for item in current_items:
            url = item["url"]
            if url in seen_set:
                continue

            adopted_items.append(item)
            new_seen.append(url)
            seen_set.add(url)

        print(f"[{SOURCE_NAME}] New: {len(adopted_items)}")
        return adopted_items, new_seen

    except Exception as e:
        print(f"[{SOURCE_NAME}] Error: {e}")
        return [], seen
