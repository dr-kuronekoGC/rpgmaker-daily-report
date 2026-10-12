"""Collect resource-related topics from Makerando's dedicated forum sections."""

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from config import MAKERANDO_FORUM_URL, MAKERANDO_SEEN_FILE
from sources.base import get_html

SEEN_FILE = MAKERANDO_SEEN_FILE
SOURCE_NAME = "Makerando IT"
BASE_URL = "https://www.makerando.com"
MAX_SECTION_PAGES = 3

# Find the relevant forum sections by their visible labels instead of relying
# on numeric forum IDs, which can change if the forum is reorganized.
SECTION_MATCHERS = (
    ("rpg maker scripting", "plugin"),
    ("plugin e addon rpg maker", "plugin"),
    ("musica e suoni", "sound"),
    ("risorse grafiche rpg maker", "graphics"),
)

GRAPHIC_KEYWORDS = (
    "risorsa", "risorse", "grafica", "grafiche", "charset", "charaset",
    "faceset", "chipset", "tileset", "battleback", "battler", "sprite",
    "pixel art", "animazione", "animazioni", "icone", "icone mz",
    "monster", "panorama", "picture", "title screen",
)
SOUND_KEYWORDS = (
    "audio", "musica", "musiche", "suono", "suoni", "sound", "bgm",
    "bgs", "sfx", "effetti sonori", "mp3", "midi", "wav", "ogg",
)
PLUGIN_KEYWORDS = (
    "plugin", "plugins", "script", "scripts", "javascript", "rgss",
    "patch", "utility", "utilità", "utilita", "tool",
)
QUESTION_KEYWORDS = (
    "richiesta", "richieste", "aiuto", "supporto", "come fare",
    "problema", "problemi", "cerco", "cerchiamo", "qualcuno sa",
    "help", "request", "requests", "support",
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


def find_section_urls(html):
    """Return the public topic-list URLs for relevant forum sections."""
    soup = BeautifulSoup(html, "html.parser")
    sections = {}

    for link in soup.select("a[href]"):
        label = " ".join(link.get_text(" ", strip=True).lower().split())
        if not label:
            continue

        for marker, section_type in SECTION_MATCHERS:
            if marker not in label:
                continue

            url = urljoin(BASE_URL + "/", link.get("href", ""))
            parts = urlparse(url)
            if parts.netloc.lower() not in {"makerando.com", "www.makerando.com"}:
                continue
            # A forum-section URL is not a topic URL itself.
            if "/topic/" in parts.path:
                continue
            sections[url.split("#", 1)[0]] = section_type
            break

    return sections


def classify(title, context="", section_type=None):
    title_text = " ".join(str(title or "").lower().split())
    text = " ".join(f"{title_text} {context}".lower().split())

    if not title_text or any(word in title_text for word in QUESTION_KEYWORDS):
        return None

    if section_type == "plugin":
        return "Makerando ITプラグイン"

    if section_type == "sound":
        if any(word in text for word in SOUND_KEYWORDS):
            return "Makerando ITサウンド素材"
        return None

    if section_type == "graphics":
        if any(word in text for word in GRAPHIC_KEYWORDS):
            return "Makerando ITグラフィック素材"
        return None

    if any(word in text for word in PLUGIN_KEYWORDS):
        return "Makerando ITプラグイン"
    if any(word in text for word in SOUND_KEYWORDS):
        return "Makerando ITサウンド素材"
    if any(word in text for word in GRAPHIC_KEYWORDS):
        return "Makerando ITグラフィック素材"
    return None


def extract_items(html, section_type=None):
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
        category = classify(title, context, section_type=section_type)
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


def get_next_page_url(html, current_url):
    soup = BeautifulSoup(html, "html.parser")
    for link in soup.select("a[rel='next'], a[aria-label*='Next'], a[title*='Next']"):
        href = link.get("href")
        if href:
            candidate = urljoin(current_url, href)
            if candidate != current_url:
                return candidate

    for link in soup.select("a[href]"):
        label = " ".join(
            " ".join([
                link.get_text(" ", strip=True),
                link.get("title", ""),
                link.get("aria-label", ""),
            ]).lower().split()
        )
        if label in {"next", "next page", "successivo", "pagina successiva", "›", "»"}:
            href = link.get("href")
            if href:
                candidate = urljoin(current_url, href)
                if candidate != current_url:
                    return candidate

    return None


def get_items(seen):
    if not isinstance(seen, list):
        seen = []

    try:
        homepage = get_html(MAKERANDO_FORUM_URL)
    except Exception as exc:
        print(f"[{SOURCE_NAME}] Homepage error: {exc}")
        return [], seen

    pages = [(MAKERANDO_FORUM_URL, None)]
    pages.extend(find_section_urls(homepage).items())
    # Deduplicate URLs while preserving order.
    unique_pages = []
    page_types = {}
    for url, section_type in pages:
        if url not in page_types:
            unique_pages.append(url)
            page_types[url] = section_type
        elif page_types[url] is None and section_type is not None:
            page_types[url] = section_type

    items_by_url = {}
    for page_url in unique_pages:
        section_type = page_types[page_url]
        current_url = page_url
        visited = set()

        for page_number in range(1, MAX_SECTION_PAGES + 1):
            if current_url in visited:
                break
            visited.add(current_url)

            try:
                html = homepage if current_url == MAKERANDO_FORUM_URL else get_html(current_url)
            except Exception as exc:
                print(f"[{SOURCE_NAME}] Section page error: {exc}")
                break

            for item in extract_items(html, section_type=section_type):
                items_by_url[item["url"]] = item

            next_url = get_next_page_url(html, current_url)
            if not next_url:
                break
            current_url = next_url

    new_seen = list(seen)
    seen_set = set(seen)
    adopted = []

    for item in items_by_url.values():
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
