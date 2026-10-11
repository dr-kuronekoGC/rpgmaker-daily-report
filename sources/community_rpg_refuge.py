"""Collector for RPG Refuge's dedicated RPG Maker resource forums.

The XenForo RSS endpoints keep collection lightweight and avoid crawling
individual creator pages. Only resource, plugin, and development-tool boards
are monitored; support/request and game-showcase sections are intentionally
excluded.
"""

from html import unescape
import re
from urllib.parse import urljoin, urlparse

import feedparser
from bs4 import BeautifulSoup

from config import RPG_REFUGE_SEEN_FILE
from sources.base import get_html


SEEN_FILE = RPG_REFUGE_SEEN_FILE
SOURCE_NAME = "RPG Refuge"
BASE_URL = "https://rpg-refuge.com"

# XenForo forum RSS endpoints. Keep the initial scope focused on actual
# resources and tools, not general discussion or support requests.
FEED_CATEGORIES = (
    (
        "https://rpg-refuge.com/forums/2d-assets.57/index.rss",
        "RPG Refugeグラフィック素材",
    ),
    (
        "https://rpg-refuge.com/forums/2d-assets.63/index.rss",
        "RPG Refugeグラフィック素材",
    ),
    (
        "https://rpg-refuge.com/forums/audio-assets.166/index.rss",
        "RPG Refugeサウンド素材",
    ),
    (
        "https://rpg-refuge.com/forums/rpg-maker-plugins.174/index.rss",
        "RPG Refugeプラグイン",
    ),
    (
        "https://rpg-refuge.com/forums/development-tools.167/index.rss",
        "RPG Refuge開発ツール",
    ),
)

EXCLUDED_TITLE_PREFIXES = (
    "template",
    "rules",
    "checklist",
    "requirements",
)


def normalize_url(url):
    """Return a canonical local thread URL, or None for non-thread links."""
    if not isinstance(url, str) or not url.strip():
        return None

    absolute = urljoin(BASE_URL + "/", url.strip())
    parts = urlparse(absolute)

    if parts.netloc.lower() not in {"rpg-refuge.com", "www.rpg-refuge.com"}:
        return None

    # XenForo thread URLs use /threads/<slug>.<numeric-id>/.
    import re

    if not re.search(r"/threads/[^/]+\.\d+/?$", parts.path):
        return None

    return f"{BASE_URL}{parts.path}".rstrip("/")


def is_excluded_title(title):
    normalized = " ".join(str(title or "").lower().split())
    return any(
        normalized.startswith(prefix)
        for prefix in EXCLUDED_TITLE_PREFIXES
    )


def parse_feed(xml_text, category):
    """Parse one RSS feed into validated resource topic records."""
    feed = feedparser.parse(xml_text)

    if getattr(feed, "bozo", False):
        detail = getattr(feed, "bozo_exception", None)

        if not feed.entries:
            # Some forums put malformed HTML inside RSS descriptions. If the
            # strict RSS parser rejects the whole document, try a tolerant
            # HTML parser before declaring the feed unusable.
            recovered_entries = []

            # Recover records from RSS <item> or Atom <entry> blocks.
            # Split at each record start rather than requiring a closing tag:
            # malformed markup in a description can break the closing XML tag.
            record_starts = list(re.finditer(
                r"<(?:item|entry)\b[^>]*>",
                xml_text,
                flags=re.IGNORECASE,
            ))
            for index, record_match in enumerate(record_starts):
                block_start = record_match.end()
                block_end = (
                    record_starts[index + 1].start()
                    if index + 1 < len(record_starts)
                    else len(xml_text)
                )
                block = xml_text[block_start:block_end]
                title_match = re.search(
                    r"<title\b[^>]*>(.*?)</title\s*>",
                    block,
                    flags=re.IGNORECASE | re.DOTALL,
                )
                link_match = re.search(
                    r"<link\b[^>]*>(.*?)</link\s*>",
                    block,
                    flags=re.IGNORECASE | re.DOTALL,
                )
                if not title_match or not link_match:
                    continue

                title = BeautifulSoup(
                    title_match.group(1), "html.parser"
                ).get_text(" ", strip=True)
                link = re.sub(
                    r"<!\[CDATA\[(.*?)\]\]>",
                    r"\1",
                    link_match.group(1),
                    flags=re.DOTALL,
                )
                link = unescape(re.sub(r"<[^>]+>", "", link).strip())
                if title and link:
                    recovered_entries.append({
                        "title": title,
                        "link": link,
                    })

            if recovered_entries:
                print(
                    f"[{SOURCE_NAME}] Recovered {len(recovered_entries)} "
                    f"entries from malformed RSS for {category}"
                )
                feed.entries = recovered_entries
            else:
                record_count = len(record_starts)
                title_count = len(re.findall(
                    r"<title\b", xml_text, flags=re.IGNORECASE
                ))
                link_count = len(re.findall(
                    r"<link\b", xml_text, flags=re.IGNORECASE
                ))
                sample = " ".join(xml_text[:240].split())
                raise ValueError(
                    f"Invalid RSS feed for {category}: "
                    f"{detail or 'no entries parsed'}; "
                    f"chars={len(xml_text)}, records={record_count}, "
                    f"title_tags={title_count}, link_tags={link_count}, "
                    f"start={sample!r}"
                )
        else:
            print(
                f"[{SOURCE_NAME}] RSS warning for {category}: "
                f"{detail or 'malformed feed'}"
            )

    items = []
    local_seen = set()

    for entry in feed.entries:
        title = str(entry.get("title") or "").strip()
        url = normalize_url(entry.get("link"))

        if not title or not url or url in local_seen:
            continue
        if is_excluded_title(title):
            continue

        local_seen.add(url)
        items.append({
            "title": title,
            "url": url,
            "category": category,
            "source": SOURCE_NAME,
            "language": "en",
        })

    return items


def get_items(seen):
    if not isinstance(seen, list):
        seen = []

    seen_set = set(seen)
    new_seen = list(seen)
    adopted = []
    discovered_urls = set()

    # Fail the collector if a feed cannot be fetched or parsed. This lets
    # main.py report a source error and prevents a partial crawl from being
    # mistaken for a complete successful run.
    for feed_url, category in FEED_CATEGORIES:
        xml_text = get_html(feed_url)
        feed_items = parse_feed(xml_text, category)

        for item in feed_items:
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
