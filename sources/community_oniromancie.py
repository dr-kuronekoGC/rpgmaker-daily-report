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


def get_detail_seen_key(url):
    return f"detail:{url}"


DETAIL_COMPLETE_KEY = "detail:COMPLETE"


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


def find_explicit_engine(text):
    """
    Oniromancieの個別ページには、
    「Script pour RPG Maker XP」
    「Logiciel : RPG Maker XP」
    のような明示的なエンジン情報がある。

    ページ全体を検索すると共通ナビゲーションの
    RPG Maker XP/VX/MV/MZまで拾ってしまうため、
    ラベル付きの記述を優先して解析する。
    """
    if not isinstance(text, str):
        return None

    normalized = " ".join(text.split())

    label_pattern = re.compile(
        r"(?:script\s+pour|logiciel\s*:?)\s*"
        r"rpg\s*maker\s*"
        r"(xp|vx\s*ace|vx|mv|mz)",
        re.IGNORECASE,
    )

    match = label_pattern.search(normalized)

    if not match:
        return None

    version = re.sub(
        r"\s+",
        " ",
        match.group(1).strip().lower(),
    )

    version_map = {
        "xp": "RPG Maker XP",
        "vx": "RPG Maker VX",
        "vx ace": "RPG Maker VX Ace",
        "mv": "RPG Maker MV",
        "mz": "RPG Maker MZ",
    }

    return version_map.get(version)


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


def _is_engine_metadata(text):
    normalized = normalize_text(text)

    return bool(
        re.search(
            r"(?:script\s+pour|logiciel\s*:?)\s*"
            r"rpg\s*maker",
            normalized,
            re.IGNORECASE,
        )
    )


def _is_metadata_or_ui_text(text):
    normalized = normalize_text(text)

    if not normalized:
        return True

    excluded_prefixes = (
        "ecrit par ",
        "écrit par ",
        "publié par ",
        "publie par ",
        "signaler un script",
        "auteur :",
        "logiciel :",
        "script pour ",
    )

    if normalized.startswith(excluded_prefixes):
        return True

    return False


def extract_detail_content(soup, title):
    """
    個別ページの「タイトル直後〜エンジン情報」の領域から
    説明文だけを抽出する。

    Oniromancieはページ共通ナビゲーションにも多数の<p>相当の
    テキストを持つため、ページ全体から最初の<p>を拾わない。
    """
    heading = None

    normalized_title = normalize_text(title)

    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        text = tag.get_text(" ", strip=True)

        if not text:
            continue

        normalized = normalize_text(text)

        if (
            normalized == normalized_title
            or (
                normalized_title
                and normalized_title in normalized
            )
        ):
            heading = tag
            break

    if heading is None:
        return [], ""

    description_parts = []
    seen_text = set()

    for element in heading.find_all_next(["p", "div"]):
        text = element.get_text(" ", strip=True)

        if not text:
            continue

        normalized = normalize_text(text)

        if normalized in seen_text:
            continue

        # ページ本文の「Script pour / Logiciel」到達で
        # 説明領域を終了する。
        if _is_engine_metadata(text):
            break

        # 作者・投稿者等のメタデータは説明文に含めない。
        if _is_metadata_or_ui_text(text):
            continue

        # 大きなdivを拾うと、その内部のpの内容を丸ごと
        # 二重に取得する可能性があるため、pを優先する。
        if element.name != "p":
            continue

        # 共通ナビやフッターらしい短いUIテキストを除外。
        if len(text) < 20:
            continue

        description_parts.append(text)
        seen_text.add(normalized)

        if len(description_parts) >= 3:
            break

    return description_parts, " ".join(description_parts)[:3000]


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

    # ページ全体ではなく、明示された
    # 「Script pour / Logiciel」情報を最優先する。
    engine = find_explicit_engine(page_text)

    if not engine:
        # 明示ラベルがない場合のみ、ページ本文領域を補助的に検索。
        description_parts, description = extract_detail_content(
            soup,
            title,
        )
        content_text = " ".join(description_parts)

        engine = find_engine(content_text)

    else:
        _, description = extract_detail_content(
            soup,
            title,
        )

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

    if description:
        item["description"] = description

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

    detail_import_complete = (
        DETAIL_COMPLETE_KEY in seen_set
    )

    detail_completed_before = sum(
        1
        for item in discovered
        if get_detail_seen_key(item["url"]) in seen_set
    )

    if not detail_import_complete:
        print(
            f"[{SOURCE_NAME}] "
            f"Detail import progress: "
            f"{detail_completed_before}/{len(discovered)}"
        )

    for item in discovered:
        url = item["url"]
        detail_seen_key = get_detail_seen_key(url)

        if detail_seen_key in seen_set:
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

        # 初期取り込み中はArchiveには保存するが、
        # 通常のSlack新着には出さない。
        if not detail_import_complete:
            detail["_suppress_report"] = True

        new_items.append(detail)

        if url not in seen_set:
            new_seen.append(url)
            seen_set.add(url)

        new_seen.append(detail_seen_key)
        seen_set.add(detail_seen_key)

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

    detail_completed_after = sum(
        1
        for item in discovered
        if get_detail_seen_key(item["url"]) in seen_set
    )

    if (
        not detail_import_complete
        and len(discovered) >= catalog_seen_count
        and detail_completed_after >= len(discovered)
    ):
        new_seen.append(DETAIL_COMPLETE_KEY)
        print(
            f"[{SOURCE_NAME}] "
            "Detail import complete."
        )
    elif not detail_import_complete:
        print(
            f"[{SOURCE_NAME}] "
            f"Detail import progress: "
            f"{detail_completed_after}/{len(discovered)}"
        )

    print(
        f"[{SOURCE_NAME}] "
        f"New: {len(new_items)}"
    )

    return new_items, new_seen
