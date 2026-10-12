"""Collect likely resource listings from RPG Maker Network."""
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from config import RPGMAKER_NET_RESOURCES_URL, RPGMAKER_NET_SEEN_FILE
from sources.base import get_html

SEEN_FILE = RPGMAKER_NET_SEEN_FILE
SOURCE_NAME = "RPG Maker Network"
BASE_URL = "https://rpgmaker.net"
MAX_PAGES = 3

RESOURCE_WORDS = (
    "resource", "resources", "asset", "assets", "tileset", "sprite",
    "character", "faceset", "music", "sound", "plugin", "script",
    "graphics", "download",
)
QUESTION_WORDS = ("request", "looking for", "help", "question", "how do i")


def normalize_url(url):
    if not isinstance(url, str) or not url.strip():
        return None
    absolute = urljoin(BASE_URL + "/", url.strip())
    parts = urlparse(absolute)
    if parts.netloc.lower() not in {"rpgmaker.net", "www.rpgmaker.net"}:
        return None
    if not parts.path or parts.path == "/":
        return None
    return absolute.split("#", 1)[0]


def extract_items(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    local_seen = set()
    for link in soup.select("a[href]"):
        title = link.get_text(" ", strip=True)
        url = normalize_url(link.get("href"))
        if not title or not url or url in local_seen:
            continue
        title_text = " ".join(title.lower().split())
        if any(word in title_text for word in QUESTION_WORDS):
            continue
        parent = link.parent
        context = parent.get_text(" ", strip=True) if parent else title
        searchable = " ".join(f"{title_text} {context.lower()}".split())
        if not any(word in searchable for word in RESOURCE_WORDS):
            continue
        if len(title) < 4 or len(title) > 180:
            continue
        items.append({
            "title": title,
            "url": url,
            "category": "RPG Maker Network素材・リソース情報",
            "source": SOURCE_NAME,
            "language": "en",
        })
        local_seen.add(url)
    return items


def get_next_page_url(html, current_url):
    soup = BeautifulSoup(html, "html.parser")
    selectors = (
        "a[rel='next']",
        "a[aria-label*='Next']",
        "a[title*='Next']",
    )
    for selector in selectors:
        link = soup.select_one(selector)
        if link is not None and link.get("href"):
            candidate = urljoin(current_url, link.get("href"))
            if candidate != current_url:
                return candidate
    for link in soup.select("a[href]"):
        label = " ".join(" ".join((
            link.get_text(" ", strip=True), link.get("title", ""),
            link.get("aria-label", ""),
        )).lower().split())
        if label in {"next", "next page", "older", "›", "»"}:
            href = link.get("href")
            if href:
                candidate = urljoin(current_url, href)
                if candidate != current_url:
                    return candidate
    return None


def get_items(seen):
    if not isinstance(seen, list):
        seen = []
    new_seen = list(seen)
    seen_set = set(seen)
    adopted = []
    current_url = RPGMAKER_NET_RESOURCES_URL
    visited = set()
    for page_number in range(1, MAX_PAGES + 1):
        if current_url in visited:
            break
        visited.add(current_url)
        try:
            html = get_html(current_url)
        except Exception as exc:
            print(f"[{SOURCE_NAME}] Page {page_number} error: {exc}")
            return [], seen
        for item in extract_items(html):
            url = item["url"]
            if url in seen_set:
                continue
            seen_set.add(url)
            new_seen.append(url)
            adopted.append(item)
        next_url = get_next_page_url(html, current_url)
        if not next_url:
            break
        current_url = next_url
    print(f"[{SOURCE_NAME}] New resource links: {len(adopted)}")
    return adopted, new_seen
