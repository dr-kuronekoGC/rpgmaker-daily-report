"""Collector for RPG Refuge's public RPG Maker resource forums.

The RSS endpoints currently return an access-challenge HTML page to GitHub
Actions. Collect thread titles from public forum listing pages instead.
"""

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from config import RPG_REFUGE_SEEN_FILE
from sources.base import get_html


SEEN_FILE = RPG_REFUGE_SEEN_FILE
SOURCE_NAME = "RPG Refuge"
BASE_URL = "https://rpg-refuge.com"

# Public XenForo forum pages (not the RSS endpoints).
FORUM_CATEGORIES = (
    ("https://rpg-refuge.com/forums/2d-assets.57/", "RPG Refugeグラフィック素材"),
    ("https://rpg-refuge.com/forums/2d-assets.63/", "RPG Refugeグラフィック素材"),
    ("https://rpg-refuge.com/forums/audio-assets.166/", "RPG Refugeサウンド素材"),
    ("https://rpg-refuge.com/forums/rpg-maker-plugins.174/", "RPG Refugeプラグイン"),
    ("https://rpg-refuge.com/forums/development-tools.167/", "RPG Refuge開発ツール"),
)

EXCLUDED_TITLE_PREFIXES = ("template", "rules", "checklist", "requirements")


def normalize_url(url):
    """Return a canonical local thread URL, or None for non-thread links."""
    if not isinstance(url, str) or not url.strip():
        return None

    absolute = urljoin(BASE_URL + "/", url.strip())
    parts = urlparse(absolute)
    if parts.netloc.lower() not in {"rpg-refuge.com", "www.rpg-refuge.com"}:
        return None
    if not re.search(r"/threads/[^/]+\.\d+/?$", parts.path):
        return None
    return f"{BASE_URL}{parts.path}".rstrip("/")


def is_excluded_title(title):
    normalized = " ".join(str(title or "").lower().split())
    return any(normalized.startswith(prefix) for prefix in EXCLUDED_TITLE_PREFIXES)


def _is_excluded_thread(title, thread_row):
    """Exclude rule/template rows identified by either title or XenForo labels."""
    if is_excluded_title(title):
        return True
    if thread_row is None:
        return False

    labels = " ".join(
        label.get_text(" ", strip=True).lower()
        for label in thread_row.select(".label, .labelLink")
    )
    return any(
        re.search(rf"(?<![a-z]){re.escape(prefix)}(?![a-z])", labels)
        for prefix in EXCLUDED_TITLE_PREFIXES
    )


def parse_forum_page(html_text, category):
    """Extract resource thread records from a public XenForo forum listing."""
    soup = BeautifulSoup(html_text, "html.parser")

    # Restrict extraction to thread-title elements so site-wide featured
    # threads, recent posts, navigation, and profile links are not collected.
    title_links = soup.select(".structItem-title a[href*='/threads/']")
    if not title_links:
        sample = " ".join(html_text[:240].split())
        thread_link_count = len(soup.select("a[href*='/threads/']"))
        page_title = soup.title.get_text(" ", strip=True) if soup.title else "none"
        raise ValueError(
            f"Could not find RPG Refuge thread listings for {category}: "
            f"chars={len(html_text)}, thread_links={thread_link_count}, "
            f"title={page_title!r}, start={sample!r}"
        )

    items = []
    local_seen = set()
    for link in title_links:
        title = link.get_text(" ", strip=True)
        url = normalize_url(link.get("href"))
        if not title or not url or url in local_seen:
            continue

        thread_row = link.find_parent(class_="structItem")
        if _is_excluded_thread(title, thread_row):
            continue

        local_seen.add(url)
        items.append({
            "title": title,
            "url": url,
            "category": category,
            "source": SOURCE_NAME,
            "language": "en",
        })

    print(f"[{SOURCE_NAME}] Parsed {len(items)} thread(s) from {category}")
    return items


def get_items(seen):
    if not isinstance(seen, list):
        seen = []

    seen_set = set(seen)
    new_seen = list(seen)
    adopted = []
    discovered_urls = set()

    # Any failed page raises an error so a partial crawl is not recorded as
    # complete. main.py therefore will not persist seen changes for this run.
    for forum_url, category in FORUM_CATEGORIES:
        html_text = get_html(forum_url)
        forum_items = parse_forum_page(html_text, category)

        for item in forum_items:
            url = item["url"]
            if url in discovered_urls:
                continue
            discovered_urls.add(url)
            if url in seen_set:
                continue

            seen_set.add(url)
            new_seen.append(url)
            adopted.append(item)

    if not seen:
        print(f"[{SOURCE_NAME}] Baseline: {len(new_seen)} topics")
        return [], new_seen

    print(f"[{SOURCE_NAME}] New: {len(adopted)}")
    return adopted, new_seen
