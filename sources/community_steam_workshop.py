"""Collect resource-tagged items from the RPG Maker MZ Steam Workshop."""

import re
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup

from config import STEAM_WORKSHOP_QUERIES, STEAM_WORKSHOP_SEEN_FILE
from sources.base import get_html


SEEN_FILE = STEAM_WORKSHOP_SEEN_FILE
SOURCE_NAME = "Steam Workshop RPG Maker MZ"
BASE_URL = "https://steamcommunity.com"
TITLE_SELECTORS = (
    ".workshopItemTitle",
    ".workshop_item_title",
    ".itemTitle",
    "[data-tooltip-text]",
)


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


def _clean_title(value):
    if not isinstance(value, str):
        return ""
    return " ".join(value.split()).strip()


def _extract_title(link):
    # Steam's browse page markup has changed over time. Prefer explicit title
    # elements, but also support title text on the link or its item card.
    for selector in TITLE_SELECTORS:
        tag = link.select_one(selector)
        if tag is not None:
            value = (
                tag.get("data-tooltip-text", "")
                or tag.get("title", "")
                or tag.get_text(" ", strip=True)
            )
            value = _clean_title(value)
            if value:
                return value

    value = _clean_title(
        link.get("data-tooltip-text", "")
        or link.get("title", "")
        or link.get("aria-label", "")
        or link.get_text(" ", strip=True)
    )
    if value:
        return value

    card = link.find_parent(
        class_=re.compile(r"workshopItem|workshop_item|workshopitem", re.I)
    )
    if card is not None:
        for selector in TITLE_SELECTORS:
            tag = card.select_one(selector)
            if tag is not None:
                value = _clean_title(
                    tag.get("data-tooltip-text", "")
                    or tag.get("title", "")
                    or tag.get_text(" ", strip=True)
                )
                if value:
                    return value

        image = card.select_one("img[alt]")
        if image is not None:
            return _clean_title(image.get("alt", ""))

    return ""


def extract_items(html, category):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    local_seen = set()

    for link in soup.select('a[href*="/sharedfiles/filedetails/"]'):
        url = normalize_url(link.get("href"))
        if not url or url in local_seen:
            continue

        title = _extract_title(link)
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
    parsed_total = 0

    for category, url in STEAM_WORKSHOP_QUERIES:
        try:
            html = get_html(url)
        except Exception as exc:
            failed += 1
            print(f"[{SOURCE_NAME}] Error ({category}): {exc}")
            continue

        page_items = extract_items(html, category)
        parsed_total += len(page_items)
        print(
            f"[{SOURCE_NAME}] Scan ({category}): "
            f"parsed={len(page_items)}"
        )

        for item in page_items:
            item_url = item["url"]
            if item_url in seen_set:
                continue
            seen_set.add(item_url)
            new_seen.append(item_url)
            adopted.append(item)

    # RPG Maker MZ's public workshop has hundreds of entries. An empty parse
    # across every category is therefore more likely to indicate changed page
    # markup or a challenge page than a genuinely empty source. Fail closed:
    # do not establish or overwrite the seen baseline with zero items.
    if parsed_total == 0:
        raise ValueError(
            "No workshop items could be parsed from any category page "
            f"(failed queries={failed}/{len(STEAM_WORKSHOP_QUERIES)}); "
            "refusing to treat this as an empty baseline"
        )

    if not seen:
        print(
            f"[{SOURCE_NAME}] Baseline: {len(new_seen)} items; "
            f"parsed={parsed_total}; failed queries={failed}"
        )
        return [], new_seen

    print(
        f"[{SOURCE_NAME}] New: {len(adopted)}; "
        f"parsed={parsed_total}; failed queries={failed}"
    )
    return adopted, new_seen
