import re

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from config import (
    RPGMAKER_UNION_RESOURCE_URL,
    RPGMAKER_UNION_PLUGIN_URL,
    RPGMAKER_UNION_SEEN_FILE,
)
from sources.base import get_html


SEEN_FILE = RPGMAKER_UNION_SEEN_FILE
SOURCE_NAME = "RPG Maker Union"
BASE_URL = "https://rpgmakerunion.ru"

SECTION_URLS = (
    (RPGMAKER_UNION_RESOURCE_URL, "resource"),
    (RPGMAKER_UNION_PLUGIN_URL, "plugin"),
)

MAX_PAGES_PER_SECTION = 3

THREAD_PATH_PATTERN = re.compile(
    r"^/threads?/[^/]+\.\d+(?:/page-\d+)?/?$",
    re.IGNORECASE,
)

QUESTION_KEYWORDS = (
    "ищу",
    "ищем",
    "нужен",
    "нужна",
    "нужно",
    "нужны",
    "поиск",
    "помощь",
    "вопрос",
    "просьба",
    "запрос",
    "как сделать",
    "как создать",
)

RESOURCE_KEYWORDS = (
    "ресурс",
    "ресурсы",
    "график",
    "спрайт",
    "тайл",
    "тайлы",
    "персонаж",
    "портрет",
    "лицо",
    "икон",
    "анимац",
    "музык",
    "звук",
    "аудио",
    "bgm",
    "bgs",
    "sfx",
    "dlc",
    "карта",
)


def normalize_text(value):
    if not isinstance(value, str):
        return ""

    return " ".join(value.lower().split())


def normalize_url(url):
    if not isinstance(url, str):
        return None

    url = url.strip()

    if not url:
        return None

    url = urljoin(BASE_URL, url)
    url = url.split("#", 1)[0]
    url = url.split("?", 1)[0]

    return url


def is_thread_url(url):
    if not url:
        return False

    path = urlparse(url).path
    return THREAD_PATH_PATTERN.match(path) is not None


def classify(title, section_type):
    text = normalize_text(title)

    if any(keyword in text for keyword in QUESTION_KEYWORDS):
        return None

    if section_type == "plugin":
        return "プラグイン"

    if any(keyword in text for keyword in RESOURCE_KEYWORDS):
        if any(keyword in text for keyword in ("музык", "звук", "аудио", "bgm", "bgs", "sfx")):
            return "サウンド素材"
        return "グラフィック素材"

    # The section itself is dedicated to graphics, music and other resources.
    # Keep the collector permissive; detailed classification happens later.
    if section_type == "resource":
        return "グラフィック素材"

    return None


THREAD_URL_IN_HTML_PATTERN = re.compile(
    r'''(?:https?:)?//rpgmakerunion\\.ru/threads?/[^"'\\s<>]+?\\.\\d+(?:/page-\\d+)?(?:[?#][^"'\\s<>]*)?''',
    re.IGNORECASE,
)


def extract_raw_thread_urls(html):
    urls = []

    # HTML/JavaScript内で \/ のようにエスケープされている場合に備える。
    normalized_html = html.replace("\\/", "/")

    for match in THREAD_URL_IN_HTML_PATTERN.finditer(normalized_html):
        raw_url = match.group(0)

        if not raw_url.startswith("http"):
            raw_url = urljoin(BASE_URL, raw_url)

        url = normalize_url(raw_url)

        if url and is_thread_url(url) and url not in urls:
            urls.append(url)

    return urls


def extract_items(html, section_type):
    soup = BeautifulSoup(html, "html.parser")

    items = []
    local_seen = set()

    # 通常のHTMLリンクをまず取得する。
    for link in soup.select("a[href]"):
        title = link.get_text(" ", strip=True)
        url = normalize_url(link.get("href"))

        if not title or not url:
            continue

        if not is_thread_url(url):
            continue

        if url in local_seen:
            continue

        category = classify(title, section_type)
        if category is None:
            continue

        items.append(
            {
                "title": title,
                "url": url,
                "category": category,
                "source": SOURCE_NAME,
            }
        )
        local_seen.add(url)

    # Unionでは、Actionsから取得したHTML内に通常の<a href>が
    # 現れないケースがあるため、HTML本文に埋め込まれた
    # /thread/...ID もフォールバックとして拾う。
    for url in extract_raw_thread_urls(html):
        if url in local_seen:
            continue

        # URLしか取得できない場合は、詳細分類を後段に任せる。
        category = "プラグイン" if section_type == "plugin" else "グラフィック素材"

        items.append(
            {
                "title": url.rsplit("/", 1)[-1],
                "url": url,
                "category": category,
                "source": SOURCE_NAME,
            }
        )
        local_seen.add(url)

    return items

def get_page_url(section_url, page_number):
    if page_number <= 1:
        return section_url

    return section_url.rstrip("/") + f"/page-{page_number}"


def get_items(seen):
    new_seen = list(seen)
    seen_set = set(seen)
    adopted_items = []

    for section_url, section_type in SECTION_URLS:
        for page_number in range(1, MAX_PAGES_PER_SECTION + 1):
            current_url = get_page_url(section_url, page_number)

            try:
                html = get_html(current_url)
            except Exception as e:
                print(
                    f"[{SOURCE_NAME}] Page {page_number} error: {e}"
                )
                break

            # 一時診断：GitHub Actionsから見えているHTMLの状態を確認する。
            # Unionだけ候補0件が続いているため、HTML構造/リダイレクト/bot対策を切り分ける。
            soup = BeautifulSoup(html, "html.parser")
            all_links = soup.select("a[href]")
            thread_links = [
                link.get("href", "")
                for link in all_links
                if "/thread" in (link.get("href", "") or "").lower()
            ]
            raw_thread_urls = extract_raw_thread_urls(html)
            print(
                f"[{SOURCE_NAME}][DEBUG] {section_type} page {page_number}: "
                f"html={len(html)} chars, links={len(all_links)}, "
                f"thread_like_links={len(thread_links)}, "
                f"raw_thread_urls={len(raw_thread_urls)}, "
                f"title={soup.title.get_text(' ', strip=True) if soup.title else ''}"
            )
            if thread_links:
                print(
                    f"[{SOURCE_NAME}][DEBUG] thread-like samples: "
                    f"{thread_links[:5]}"
                )
            if raw_thread_urls:
                print(
                    f"[{SOURCE_NAME}][DEBUG] raw thread samples: "
                    f"{raw_thread_urls[:5]}"
                )

            page_items = extract_items(html, section_type)

            print(
                f"[{SOURCE_NAME}] {section_type} "
                f"page {page_number}: {len(page_items)} candidate threads"
            )

            for item in page_items:
                url = item["url"]

                if url in seen_set:
                    continue

                new_seen.append(url)
                seen_set.add(url)
                adopted_items.append(item)

                print(
                    f"[{SOURCE_NAME}][{item['category']}] "
                    f"{item['title']}"
                )

    if not seen:
        print(
            f"[{SOURCE_NAME}] Baseline: {len(new_seen)} items"
        )
        return [], new_seen

    print(f"[{SOURCE_NAME}] New: {len(adopted_items)}")
    return adopted_items, new_seen
