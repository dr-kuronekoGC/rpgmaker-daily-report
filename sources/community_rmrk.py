"""Collect resource topics from RMRK's resource database.

RMRK has announced that it may close after 2026, so this collector includes
older resource topics rather than suppressing the first scan as a baseline.
"""
import re
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from config import RMRK_RESOURCE_URL, RMRK_SEEN_FILE
from sources.base import get_html

SEEN_FILE = RMRK_SEEN_FILE
SOURCE_NAME = "RMRK"
BASE_URL = "https://rmrk.net"
MAX_PAGES_PER_SECTION = 3

SOUND_KEYWORDS = ("audio", "sound", "music", "bgm", "bgs", "sfx", "sound effect")
PLUGIN_KEYWORDS = ("plugin", "script", "rgss", "javascript", "event system")
GRAPHIC_KEYWORDS = (
    "graphic", "sprite", "charset", "faceset", "tileset", "battler",
    "icon", "pixel", "animation", "map", "character", "background",
)
QUESTION_KEYWORDS = ("request", "looking for", "need help", "question", "help me")


def normalize_url(url):
    if not isinstance(url, str) or not url.strip():
        return None
    absolute = urljoin(BASE_URL + "/", url.strip())
    parts = urlparse(absolute)
    if parts.netloc.lower() not in {"rmrk.net", "www.rmrk.net"}:
        return None
    match = re.search(r"topic[=,](\d+)", absolute)
    if match:
        return f"{BASE_URL}/index.php?topic={match.group(1)}.0"
    return None


def classify(title):
    text = " ".join(str(title or "").lower().split())
    if not text or any(word in text for word in QUESTION_KEYWORDS):
        return None
    if any(word in text for word in PLUGIN_KEYWORDS):
        return "RMRKプラグイン・スクリプト"
    if any(word in text for word in SOUND_KEYWORDS):
        return "RMRKサウンド素材"
    if any(word in text for word in GRAPHIC_KEYWORDS):
        return "RMRKグラフィック素材"
    # This is a dedicated completed-resource board, so otherwise-unspecified
    # topics are still material leads rather than general forum discussions.
    return "RMRK素材情報"


def extract_items(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    local_seen = set()
    selectors = (
        "span.subject a[href]",
        "td.subject a[href]",
        "a[href*='topic=']",
        "a[href*='topic,']",
    )
    links = []
    for selector in selectors:
        links = soup.select(selector)
        if links:
            break
    for link in links:
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
            "language": "en",
        })
        local_seen.add(url)
    return items


def get_next_page_url(html, current_url):
    soup = BeautifulSoup(html, "html.parser")
    current_parts = urlparse(current_url)
    current_query = parse_qs(current_parts.query)
    current_board = current_query.get("board", [None])[0]
    board_match = re.fullmatch(r"(\d+)\.(\d+)", current_board or "")
    if board_match:
        board_id = board_match.group(1)
        current_offset = int(board_match.group(2))
        candidates = []
        for link in soup.select("a[href]"):
            href = link.get("href")
            if not href:
                continue
            candidate = urljoin(current_url, href)
            query = parse_qs(urlparse(candidate).query)
            board_value = query.get("board", [None])[0]
            match = re.fullmatch(r"(\d+)\.(\d+)", board_value or "")
            if match and match.group(1) == board_id:
                offset = int(match.group(2))
                if offset > current_offset:
                    candidates.append((offset, candidate))
        if candidates:
            return min(candidates, key=lambda pair: pair[0])[1]

    for link in soup.select("a[href]"):
        label = " ".join(" ".join((
            link.get_text(" ", strip=True),
            link.get("title", ""),
            link.get("aria-label", ""),
        )).lower().split())
        if label in {"next", "next page", "›", "»"} or "next page" in label:
            href = link.get("href")
            if href:
                candidate = urljoin(current_url, href)
                if candidate != current_url:
                    return candidate
    return None


def find_resource_sections(html):
    soup = BeautifulSoup(html, "html.parser")
    sections = {RMRK_RESOURCE_URL: "resource"}
    for link in soup.select("a[href]"):
        label = " ".join(link.get_text(" ", strip=True).lower().split())
        if label not in {"graphics", "audio & video", "miscellaneous"}:
            continue
        href = link.get("href")
        if href:
            sections[urljoin(BASE_URL + "/", href)] = label
    return list(sections)


def get_items(seen):
    if not isinstance(seen, list):
        seen = []
    new_seen = list(seen)
    seen_set = set(seen)
    adopted = []
    try:
        html = get_html(RMRK_RESOURCE_URL)
    except Exception as exc:
        print(f"[{SOURCE_NAME}] Resource board error: {exc}")
        return [], seen

    section_urls = find_resource_sections(html)
    for section_url in section_urls:
        current_url = section_url
        visited = set()
        for page_number in range(MAX_PAGES_PER_SECTION):
            if current_url in visited:
                break
            visited.add(current_url)
            try:
                page_html = html if current_url == RMRK_RESOURCE_URL else get_html(current_url)
            except Exception as exc:
                print(f"[{SOURCE_NAME}] Section page error: {exc}")
                break
            for item in extract_items(page_html):
                url = item["url"]
                if url in seen_set:
                    continue
                seen_set.add(url)
                new_seen.append(url)
                adopted.append(item)
            next_url = get_next_page_url(page_html, current_url)
            if not next_url:
                break
            current_url = next_url

    print(f"[{SOURCE_NAME}] Resource topics collected: {len(adopted)}")
    return adopted, new_seen
