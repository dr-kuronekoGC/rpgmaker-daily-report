import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from config import (
    ONIROMANCIE_SCRIPTS_URL,
    ONIROMANCIE_SEEN_FILE,
)
from sources.base import get_html


SEEN_FILE = ONIROMANCIE_SEEN_FILE
SOURCE_NAME = "Oniromancie"

BASE_URL = "https://www.rpg-maker.fr"

MAX_DISCOVERY_PAGES = 50
MAX_DETAIL_FETCHES = 20

ENGINE_PATTERNS = (
    ("RPG Maker XP", ("rpg maker xp", "rmxp")),
    ("RPG Maker VX Ace", ("rpg maker vx ace", "vx ace")),
    ("RPG Maker VX", ("rpg maker vx",)),
    ("RPG Maker MV", ("rpg maker mv",)),
    ("RPG Maker MZ", ("rpg maker mz",)),
)

CATEGORY_PATTERNS = (
    ("人物・クラス", ("personnages et classes",)),
    ("戦闘", ("combat",)),
    ("移動・乗り物", ("mouvement et véhicules", "mouvement et vehicules")),
    ("音楽・サウンド", ("son et musique",)),
    ("マップ", ("maps",)),
    ("メニュー・タイトル・Game Over", ("menu/ecran titre/game over",)),
    ("メッセージ", ("messages",)),
    ("スキル・装備", ("compétences / equipement", "competences / equipement")),
    ("その他", ("divers",)),
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

    return urljoin(
        BASE_URL + "/",
        url,
    ).split("#", 1)[0]


def is_same_site(url):
    try:
        return urlparse(url).netloc.lower() in {
            "rpg-maker.fr",
            "www.rpg-maker.fr",
        }
    except Exception:
        return False


def is_category_url(url):
    if not is_same_site(url):
        return False

    parsed = urlparse(url)
    path = parsed.path.lower()
    query = parsed.query

    return (
        path.startswith("/scripts-pour-")
        and path.endswith(".html")
        and "id=" not in query
    )


def get_item_id(url):
    if not isinstance(url, str):
        return None

    path = urlparse(url).path

    match = re.search(
        r"/scripts-(\d+)-[^/]+\.html$",
        path,
        re.IGNORECASE,
    )

    if match:
        return match.group(1)

    return None


def is_item_url(url):
    if not is_same_site(url):
        return False

    path = urlparse(url).path

    return bool(
        re.fullmatch(
            r"/scripts-\d+-[^/]+\.html",
            path,
            re.IGNORECASE,
        )
    )


def discover_category_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    local_seen = set()

    for link in soup.select("a[href]"):
        url = normalize_url(link.get("href"))

        if not url or url in local_seen:
            continue

        if not is_category_url(url):
            continue

        links.append(url)
        local_seen.add(url)

    return links


def extract_item_links(html, fallback_category=None):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    local_seen = set()

    for link in soup.select("a[href]"):
        title = link.get_text(" ", strip=True)
        url = normalize_url(link.get("href"))

        if not title or not url:
            continue

        if not is_item_url(url):
            continue

        if url in local_seen:
            continue

        item_id = get_item_id(url)

        if not item_id:
            continue

        item = {
            "title": title,
            "url": url,
            "source_item_id": item_id,
        }

        if fallback_category:
            item["source_category"] = fallback_category

        items.append(item)
        local_seen.add(url)

    return items


def find_engine(text):
    normalized = normalize_text(text)

    for engine, patterns in ENGINE_PATTERNS:
        if any(pattern in normalized for pattern in patterns):
            return engine

    return None


def find_category(text):
    normalized = normalize_text(text)

    for category, patterns in CATEGORY_PATTERNS:
        if any(pattern in normalized for pattern in patterns):
            return category

    return None


def extract_category_from_page(html):
    soup = BeautifulSoup(html, "html.parser")

    heading_texts = []

    for tag in soup.find_all(
        ["h1", "h2", "h3", "h4", "title"]
    ):
        text = tag.get_text(" ", strip=True)
        if text:
            heading_texts.append(text)

    for text in heading_texts:
        category = find_category(text)
        if category:
            return category

    return None


def extract_detail(
    url,
    fallback_title="",
    fallback_category=None,
):
    try:
        html = get_html(url)
    except Exception as e:
        print(
            f"[{SOURCE_NAME}] Detail error: "
            f"{url} / {e}"
        )
        return None

    soup = BeautifulSoup(html, "html.parser")

    page_text = soup.get_text(
        " ",
        strip=True,
    )

    title = fallback_title

    for selector in ("h1", "h2"):
        heading = soup.select_one(selector)
        if heading:
            candidate = heading.get_text(
                " ",
                strip=True,
            )
            if candidate:
                title = candidate
                break

    if not title:
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(
                " ",
                strip=True,
            )

    item = {
        "title": title,
        "url": url,
        "source": SOURCE_NAME,
        "category": "プラグイン",
        "source_item_id": get_item_id(url),
        "source_tags": [],
    }

    engine = find_engine(page_text)

    if engine:
        item["engine"] = engine

    category = fallback_category or extract_category_from_page(html)

    if category:
        item["source_tags"].append(
            f"Oniromancie:{category}"
        )

    author_match = re.search(
        r"(?:Écrit par|Ecrit par)\s+(.+?)(?:Publié par|Signaler un script|\n|$)",
        page_text,
        re.IGNORECASE,
    )

    if author_match:
        author = author_match.group(1).strip()
        if author:
            item["author"] = author

    date_match = re.search(
        r"(?:Écrit le|Ecrit le)\s+(\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})",
        page_text,
        re.IGNORECASE,
    )

    if date_match:
        item["source_published_at"] = date_match.group(1)

    paragraphs = [
        p.get_text(" ", strip=True)
        for p in soup.find_all("p")
    ]

    paragraphs = [
        p for p in paragraphs
        if len(p) >= 20
    ]

    if paragraphs:
        item["description"] = " ".join(
            paragraphs[:3]
        )[:3000]

    return item


def discover_catalog():
    """
    Scripts/Plugins DBのカテゴリページを自動発見する。

    Oniromancieのトップページからカテゴリ一覧を辿り、
    各カテゴリページに掲載された個別スクリプトを収集する。
    """

    root_url = normalize_url(ONIROMANCIE_SCRIPTS_URL)

    queue = [
        (root_url, 0)
    ]
    queued = {root_url}
    visited = set()
    category_pages = []
    item_links = {}

    while queue and len(visited) < MAX_DISCOVERY_PAGES:
        url, depth = queue.pop(0)

        if url in visited:
            continue

        visited.add(url)

        try:
            html = get_html(url)
        except Exception as e:
            print(
                f"[{SOURCE_NAME}] "
                f"Discovery error: {url} / {e}"
            )
            continue

        category = None

        if is_category_url(url):
            category = extract_category_from_page(html)

        page_items = extract_item_links(
            html,
            fallback_category=category,
        )

        for item in page_items:
            existing = item_links.get(item["url"])

            if existing is None:
                item_links[item["url"]] = item
                continue

            if (
                not existing.get("source_category")
                and item.get("source_category")
            ):
                existing["source_category"] = (
                    item["source_category"]
                )

        if is_category_url(url):
            category_pages.append(url)

        if depth >= 2:
            continue

        for next_url in discover_category_links(html):
            if next_url in visited or next_url in queued:
                continue

            queued.add(next_url)
            queue.append(
                (
                    next_url,
                    depth + 1,
                )
            )

    print(
        f"[{SOURCE_NAME}] "
        f"Catalog pages: {len(category_pages)}"
    )
    print(
        f"[{SOURCE_NAME}] "
        f"Catalog items: {len(item_links)}"
    )

    return list(item_links.values())


def get_items(seen):
    seen_set = set(seen)

    discovered = discover_catalog()

    discovered_urls = {
        item["url"]
        for item in discovered
    }

    catalog_seen_count = sum(
        1
        for url in seen
        if is_item_url(url)
    )

    # 直前のcollectorは探索条件の不具合により
    # 13件だけをbaseline登録してしまった。
    # その不完全なbaselineを今回の正しい全件baselineへ移行する。
    has_catalog_seen = catalog_seen_count >= 100

    if not has_catalog_seen:
        new_seen = list(seen)

        for url in discovered_urls:
            if url not in seen_set:
                new_seen.append(url)

        print(
            f"[{SOURCE_NAME}] "
            f"Catalog baseline: {len(discovered)} items"
        )

        return [], new_seen

    new_items = []
    new_seen = list(seen)

    for item in discovered:
        url = item["url"]

        if url in seen_set:
            continue

        detail = extract_detail(
            url,
            fallback_title=item["title"],
            fallback_category=item.get(
                "source_category"
            ),
        )

        if detail is None:
            continue

        new_items.append(detail)
        new_seen.append(url)
        seen_set.add(url)

        print(
            f"[{SOURCE_NAME}]"
            f"[{detail.get('category')}] "
            f"{detail.get('title')}"
        )

        if len(new_items) >= MAX_DETAIL_FETCHES:
            print(
                f"[{SOURCE_NAME}] "
                f"Detail fetch limit reached: "
                f"{MAX_DETAIL_FETCHES}"
            )
            break

    print(
        f"[{SOURCE_NAME}] "
        f"New: {len(new_items)}"
    )

    return new_items, new_seen
