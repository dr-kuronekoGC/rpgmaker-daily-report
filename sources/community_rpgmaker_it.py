"""Collect plugin, graphics, and sound-resource posts from Rpg²S."""

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from config import (
    RPGMAKER_IT_FORUM_HOME,
    RPGMAKER_IT_MZ_PLUGIN_URL,
    RPGMAKER_IT_MV_PLUGIN_URL,
    RPGMAKER_IT_SEEN_FILE,
)
from sources.base import get_html


SEEN_FILE = RPGMAKER_IT_SEEN_FILE
SOURCE_NAME = "Rpg2S IT"
BASE_URL = "https://www.rpg2s.it"
MAX_SECTION_PAGES = 2

QUESTION_MARKERS = (
    "richiesta", "richieste", "aiuto", "supporto", "come fare",
    "problema", "problemi", "regolamento", "cerco", "cercasi",
)
GRAPHIC_KEYWORDS = (
    "grafica", "grafiche", "risorsa", "risorse", "tileset", "charset",
    "faceset", "chipset", "sprite", "sprites", "battler", "battleback",
    "animazione", "animazioni", "pixel art", "icone", "icona", "mappe",
    "picture", "panorama", "title screen", "monster",
)
SOUND_KEYWORDS = (
    "audio", "musica", "musiche", "suono", "suoni", "sound", "bgm",
    "bgs", "sfx", "effetti sonori", "mp3", "midi", "wav", "ogg",
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


def find_section_urls(html):
    """Discover relevant section URLs by their visible forum labels."""
    soup = BeautifulSoup(html, "html.parser")
    sections = {}

    for link in soup.select("a[href]"):
        label = " ".join(link.get_text(" ", strip=True).lower().split())
        if not label:
            continue

        section_type = None
        if label.startswith("donazione risorse grafiche ") and label.rsplit(" ", 1)[-1] in {"mz", "mv"}:
            section_type = "graphics"
        elif label == "donazione risorse sonore":
            section_type = "sound"

        if section_type is None:
            continue

        url = urljoin(BASE_URL + "/", link.get("href", ""))
        parts = urlparse(url)
        if parts.netloc.lower() not in {"rpg2s.it", "www.rpg2s.it"}:
            continue
        if "/topic/" in url:
            continue
        sections[url.split("#", 1)[0]] = section_type

    return sections


def classify(title, section_type=None):
    text = " ".join(str(title or "").lower().split())
    if not text or any(marker in text for marker in QUESTION_MARKERS):
        return None

    if section_type == "plugin":
        return "Rpg2S ITプラグイン"
    if section_type == "sound":
        return "Rpg2S ITサウンド素材"
    if section_type == "graphics":
        if any(marker in text for marker in GRAPHIC_KEYWORDS):
            return "Rpg2S ITグラフィック素材"
        return None

    # Retain the existing conservative behavior for the dedicated MZ plugin board.
    if "plugin" in text or "script" in text or "javascript" in text:
        return "Rpg2S ITプラグイン"
    if any(marker in text for marker in ("audio manager", "animazione", "battaglia", "finestra")):
        return "Rpg2S ITプラグイン"
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

        category = classify(title, section_type=section_type)
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
        label = " ".join(
            " ".join([
                link.get_text(" ", strip=True),
                link.get("title", ""),
                link.get("aria-label", ""),
            ]).lower().split()
        )
        if label in {"next", "successivo", "pagina successiva", "›", "»"}:
            candidate = urljoin(current_url, link.get("href"))
            if candidate != current_url:
                return candidate
    return None


def get_items(seen):
    if not isinstance(seen, list):
        seen = []

    try:
        homepage = get_html(RPGMAKER_IT_FORUM_HOME)
    except Exception as exc:
        print(f"[{SOURCE_NAME}] Homepage error: {exc}")
        homepage = ""

    pages = [
        (RPGMAKER_IT_MZ_PLUGIN_URL, "plugin"),
        (RPGMAKER_IT_MV_PLUGIN_URL, "plugin"),
    ]
    if homepage:
        pages.extend(find_section_urls(homepage).items())

    new_seen = list(seen)
    seen_set = set(seen)
    adopted_by_url = {}

    for start_url, section_type in pages:
        current_url = start_url
        visited = set()

        for page_number in range(1, MAX_SECTION_PAGES + 1):
            if current_url in visited:
                break
            visited.add(current_url)

            try:
                html = homepage if current_url == RPGMAKER_IT_FORUM_HOME else get_html(current_url)
            except Exception as exc:
                print(f"[{SOURCE_NAME}] Section page error: {exc}")
                break

            for item in extract_items(html, section_type=section_type):
                adopted_by_url[item["url"]] = item

            next_url = get_next_page_url(html, current_url)
            if not next_url:
                break
            current_url = next_url

    for url, item in adopted_by_url.items():
        if url in seen_set:
            continue
        new_seen.append(url)
        seen_set.add(url)

    if not seen:
        print(f"[{SOURCE_NAME}] Baseline: {len(new_seen)} items")
        return [], new_seen

    adopted = [
        item for url, item in adopted_by_url.items()
        if url in seen_set and url not in set(seen)
    ]
    print(f"[{SOURCE_NAME}] New resource topics: {len(adopted)}")
    return adopted, new_seen
