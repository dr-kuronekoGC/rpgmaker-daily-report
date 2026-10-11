import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from config import (
    RPGMAKER_FR_RESOURCE_URL,
    RPGMAKER_FR_SEEN_FILE,
)
from sources.base import get_html


SEEN_FILE = RPGMAKER_FR_SEEN_FILE
SOURCE_NAME = "RPG Maker - La Communauté FR"
BASE_URL = "https://forum.rpgmakervx-fr.com"
MAX_PAGES = 3

QUESTION_KEYWORDS = (
    "recherche", "cherche", "recherchons", "besoin de",
    "aide", "question", "comment faire", "comment créer",
    "comment creer", "problème", "probleme",
)
SOUND_KEYWORDS = (
    "musique", "son", "sons", "audio", "bgm", "bgs", "sfx",
)
GRAPHIC_KEYWORDS = (
    "charas", "faces", "tileset", "tilesets", "graphisme",
    "graphismes", "sprite", "sprites", "portrait", "icône",
    "icone", "ressource", "ressources", "animation",
)
PLUGIN_KEYWORDS = (
    "plugin", "plugins", "script", "scripts", "logiciel",
    "utilitaire", "utilitaires",
)


def normalize_url(url):
    if not isinstance(url, str) or not url.strip():
        return None
    absolute = urljoin(BASE_URL + "/", url.strip())
    parts = urlparse(absolute)
    if parts.netloc.lower() not in {
        "forum.rpgmakervx-fr.com",
        "www.rpgmakervx-fr.com",
        "rpgmakervx-fr.com",
    }:
        return None
    if not re.search(r"/t\d+(?:-|$)", parts.path):
        return None
    return f"https://forum.rpgmakervx-fr.com{parts.path}".rstrip("/")


def classify(title, forum_context=""):
    text = " ".join(f"{title} {forum_context}".lower().split())
    title_text = " ".join(title.lower().split())

    if any(word in title_text for word in QUESTION_KEYWORDS):
        return None
    if any(word in text for word in PLUGIN_KEYWORDS):
        return "RPG Maker FRプラグイン"
    if any(word in text for word in SOUND_KEYWORDS):
        return "RPG Maker FRサウンド素材"
    if any(word in text for word in GRAPHIC_KEYWORDS):
        return "RPG Maker FRグラフィック素材"

    # This collector is restricted to the forum's Resources section.
    # Ambiguous topics are omitted rather than guessed to be assets.
    return None


def extract_items(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    seen_urls = set()

    for link in soup.select("a[href]"):
        title = link.get_text(" ", strip=True)
        url = normalize_url(link.get("href"))
        if not title or not url or url in seen_urls:
            continue

        parent_text = ""
        parent = link.parent
        if parent:
            parent_text = parent.get_text(" ", strip=True)
        category = classify(title, parent_text)
        if category is None:
            continue

        items.append({
            "title": title,
            "url": url,
            "category": category,
            "source": SOURCE_NAME,
            "language": "fr",
        })
        seen_urls.add(url)

    return items


def get_next_page_url(html, current_url):
    soup = BeautifulSoup(html, "html.parser")
    for selector in (
        "a[rel='next']",
        "a.pagination_next",
        "a[href*='start=']",
        "a[href*='-p']",
    ):
        for link in soup.select(selector):
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
    current_url = RPGMAKER_FR_RESOURCE_URL
    visited_pages = set()

    for page in range(1, MAX_PAGES + 1):
        if current_url in visited_pages:
            break
        visited_pages.add(current_url)

        try:
            html = get_html(current_url)
        except Exception as e:
            print(f"[{SOURCE_NAME}] Page {page} error: {e}")
            break

        items = extract_items(html)
        for item in items:
            url = item["url"]
            if url in seen_set:
                continue
            new_seen.append(url)
            seen_set.add(url)
            adopted.append(item)

        next_url = get_next_page_url(html, current_url)
        if not next_url:
            break
        current_url = next_url

    if not seen:
        print(f"[{SOURCE_NAME}] Baseline: {len(new_seen)} items")
        return [], new_seen

    print(f"[{SOURCE_NAME}] New: {len(adopted)}")
    return adopted, new_seen
