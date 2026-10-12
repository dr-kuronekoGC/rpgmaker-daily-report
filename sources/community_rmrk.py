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
MAX_BACKFILL_PAGES_PER_SECTION = 2
CURSOR_PREFIX = "__RMRK_CURSOR__|"
DONE_PREFIX = "__RMRK_BACKFILL_DONE__|"

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


def _read_backfill_state(seen):
    """Separate ordinary topic URLs from persistent pagination metadata."""
    topic_urls = set()
    cursors = {}
    done_sections = set()
    for entry in seen:
        if not isinstance(entry, str):
            continue
        if entry.startswith(CURSOR_PREFIX):
            parts = entry.split("|", 2)
            if len(parts) == 3 and parts[1] and parts[2]:
                cursors[parts[1]] = parts[2]
        elif entry.startswith(DONE_PREFIX):
            section_url = entry[len(DONE_PREFIX):]
            if section_url:
                done_sections.add(section_url)
        else:
            topic_urls.add(entry)
    return topic_urls, cursors, done_sections


def _store_backfill_state(new_seen, topic_urls, cursors, done_sections):
    """Store cursor metadata in the source-local state without exposing it as items."""
    result = [entry for entry in new_seen if isinstance(entry, str)
              and not entry.startswith(CURSOR_PREFIX)
              and not entry.startswith(DONE_PREFIX)]
    result.extend(sorted(topic_urls - set(result)))
    result.extend(
        f"{CURSOR_PREFIX}{section_url}|{next_url}"
        for section_url, next_url in sorted(cursors.items())
        if section_url and next_url
    )
    result.extend(f"{DONE_PREFIX}{section_url}" for section_url in sorted(done_sections))
    return result


def get_items(seen):
    if not isinstance(seen, list):
        seen = []
    new_seen = list(seen)
    topic_urls, cursors, done_sections = _read_backfill_state(seen)
    adopted = []

    try:
        root_html = get_html(RMRK_RESOURCE_URL)
    except Exception as exc:
        print(f"[{SOURCE_NAME}] Resource board error: {exc}")
        return [], seen

    section_urls = find_resource_sections(root_html)
    for section_url in section_urls:
        # Check the newest page every run so new topics keep being detected.
        try:
            latest_html = root_html if section_url == RMRK_RESOURCE_URL else get_html(section_url)
        except Exception as exc:
            print(f"[{SOURCE_NAME}] Section page error: {exc}")
            continue

        def collect_page(page_html):
            for item in extract_items(page_html):
                url = item["url"]
                if url in topic_urls:
                    continue
                topic_urls.add(url)
                adopted.append(item)

        collect_page(latest_html)
        if section_url in done_sections:
            continue

        # First run starts at page 2; subsequent runs resume at the saved cursor.
        current_url = cursors.get(section_url)
        if not current_url:
            current_url = get_next_page_url(latest_html, section_url)
        if not current_url:
            done_sections.add(section_url)
            cursors.pop(section_url, None)
            continue

        visited = {section_url}
        failed = False
        for _ in range(MAX_BACKFILL_PAGES_PER_SECTION):
            if current_url in visited:
                done_sections.add(section_url)
                cursors.pop(section_url, None)
                break
            visited.add(current_url)
            try:
                page_html = get_html(current_url)
            except Exception as exc:
                print(f"[{SOURCE_NAME}] Backfill page error: {exc}")
                failed = True
                break

            collect_page(page_html)
            next_url = get_next_page_url(page_html, current_url)
            if not next_url or next_url in visited:
                done_sections.add(section_url)
                cursors.pop(section_url, None)
                break
            current_url = next_url
            cursors[section_url] = current_url

        # If a page fails, keep the cursor pointing at it for retry next run.
        if failed:
            continue

    new_seen = _store_backfill_state(new_seen, topic_urls, cursors, done_sections)
    print(f"[{SOURCE_NAME}] Resource topics collected: {len(adopted)}")
    return adopted, new_seen
