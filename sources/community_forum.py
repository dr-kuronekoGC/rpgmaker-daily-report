import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import (
    FORUM_URL,
    REQUEST_TIMEOUT,
)


# ==========================================
# Settings
# ==========================================

FORUM_BASE_URL = "https://forums.rpgmakerweb.com"

VAULT_DIR = Path("data/forum_vault")
INDEX_FILE = VAULT_DIR / "forum_index.json"
PROGRESS_FILE = Path("forum_vault_progress.json")

# 1回のActionで処理する検索語数
SEARCH_KEYWORDS_PER_RUN = 3

# 1検索語あたりに確認する最大ページ数
SEARCH_PAGES_PER_KEYWORD = 3

# Forum検索に使用するキーワード
SEARCH_KEYWORDS = [
    "RPG Maker MZ",
    "RPG Maker MV",
    "RPG Maker VX Ace",
    "RPG Maker XP",
    "RPG Maker 2003",
    "RPG Maker 2000",
    "RPG Maker plugin",
    "RPG Maker resource",
    "RPG Maker tileset",
    "RPG Maker sprite",
    "RPG Maker tutorial",
]


# ==========================================
# HTTP
# ==========================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/138.0 Safari/537.36"
    )
}


def create_session():
    """
    Forum検索用Sessionを作成する。
    """

    session = requests.Session()
    session.headers.update(HEADERS)

    return session


# ==========================================
# Progress
# ==========================================

def default_progress():
    """
    初期状態の進捗情報を返す。
    """

    today = datetime.now().date()

    initial_date = (
        today - timedelta(days=30)
    ).isoformat()

    return {
        "older_than": initial_date,
        "keyword_index": 0,
        "completed": False,
    }


def load_progress():
    """
    Forum Vaultの進捗を読み込む。
    """

    if not PROGRESS_FILE.exists():
        return default_progress()

    try:
        with PROGRESS_FILE.open(
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

    except (
        json.JSONDecodeError,
        OSError,
    ):
        return default_progress()

    if not isinstance(data, dict):
        return default_progress()

    return data


def save_progress(progress):
    """
    Forum Vaultの進捗を保存する。
    """

    with PROGRESS_FILE.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            progress,
            f,
            indent=2,
            ensure_ascii=False,
        )


# ==========================================
# Archive Index
# ==========================================

def load_index():
    """
    Forum VaultのURL indexを読み込む。
    """

    if not INDEX_FILE.exists():
        return []

    try:
        with INDEX_FILE.open(
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

    except (
        json.JSONDecodeError,
        OSError,
    ):
        return []

    if not isinstance(data, list):
        return []

    return data


def save_index(index):
    """
    Forum VaultのURL indexを保存する。
    """

    VAULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with INDEX_FILE.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            index,
            f,
            indent=2,
            ensure_ascii=False,
        )


# ==========================================
# URL
# ==========================================

def normalize_url(url):
    """
    Forum URLを正式なスレッドURLへ正規化する。

    例：

    /threads/example.123/post-456
        ↓
    /threads/example.123/

    /threads/example.123/page-2
        ↓
    /threads/example.123/

    queryやfragmentも削除する。
    """

    if not isinstance(url, str):
        return None

    url = url.strip()

    if not url:
        return None

    if url.startswith("/"):
        url = urljoin(
            FORUM_BASE_URL,
            url,
        )

    # fragmentを削除
    url = url.split("#", 1)[0]

    # queryを削除
    url = url.split("?", 1)[0]

    # /post-123 を削除
    url = re.sub(
        r"/post-\d+/?$",
        "/",
        url,
        flags=re.IGNORECASE,
    )

    # /page-2 などを削除
    url = re.sub(
        r"/page-\d+/?$",
        "/",
        url,
        flags=re.IGNORECASE,
    )

    # /threads/ で終わるURLは末尾を / に統一
    if "/threads/" in url:
        url = url.rstrip("/") + "/"

    return url


def is_thread_url(url):
    """
    RPG Maker Web Forumの正式なスレッドURLか判定する。
    """

    if not isinstance(url, str):
        return False

    return (
        "/threads/" in url
        and "/page-" not in url
        and "/post-" not in url
    )


def normalize_existing_index(index):
    """
    既存indexを正規化し、URL重複を削除する。

    戻り値：
        normalized_index
        normalized_count
        duplicate_count
    """

    normalized_index = []
    seen_urls = set()

    normalized_count = 0
    duplicate_count = 0

    for item in index:

        if not isinstance(item, dict):
            continue

        original_url = item.get("url")

        normalized_url = normalize_url(
            original_url
        )

        if not normalized_url:
            continue

        # スレッドURLとして扱えないものは除外
        if not is_thread_url(
            normalized_url
        ):
            continue

        if normalized_url != original_url:
            normalized_count += 1

        if normalized_url in seen_urls:
            duplicate_count += 1
            continue

        new_item = dict(item)

        new_item["url"] = normalized_url

        # 旧URLを記録しておく
        if (
            original_url
            and original_url != normalized_url
            and "original_url" not in new_item
        ):
            new_item["original_url"] = original_url

        normalized_index.append(
            new_item
        )

        seen_urls.add(
            normalized_url
        )

    return (
        normalized_index,
        normalized_count,
        duplicate_count,
    )


# ==========================================
# Search Form
# ==========================================

def get_search_form(session):
    """
    Forum検索ページから検索フォームを取得する。

    XenForoのCSRF token等を含むhidden fieldを
    そのまま利用する。
    """

    search_url = (
        f"{FORUM_BASE_URL}/search/"
    )

    try:

        response = session.get(
            search_url,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

    except requests.RequestException as e:

        print(
            "[Forum Vault] "
            f"Search page error: {e}"
        )

        return None

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    form = soup.find(
        "form",
        action=re.compile(
            r"/search/search"
        ),
    )

    if form is None:

        print(
            "[Forum Vault] "
            "Search form not found."
        )

        return None

    return form


# ==========================================
# Search
# ==========================================

def search_forum(
    session,
    keyword,
    older_than,
):
    """
    Forumをキーワード検索する。

    older_thanより前の投稿を対象とする。
    """

    form = get_search_form(
        session
    )

    if form is None:
        return None, None

    payload = {}

    # hidden fieldsを引き継ぐ
    for input_tag in form.find_all(
        "input"
    ):

        name = input_tag.get(
            "name"
        )

        if not name:
            continue

        payload[name] = (
            input_tag.get(
                "value",
                "",
            )
        )

    payload.update(
        {
            "keywords": keyword,
            "c[title_only]": "0",
            "c[users]": "",
            "c[newer_than]": "",
            "c[older_than]": older_than,
            "order": "date",
            "search_type": "post",
        }
    )

    action = form.get(
        "action",
        "/search/search",
    )

    search_url = urljoin(
        FORUM_BASE_URL,
        action,
    )

    try:

        response = session.post(
            search_url,
            data=payload,
            timeout=REQUEST_TIMEOUT,
        )

    except requests.RequestException as e:

        print(
            "[Forum Vault] "
            f"Search request error: {e}"
        )

        return None, None

    if response.status_code >= 400:

        print(
            "[Forum Vault] "
            f"Search HTTP error: "
            f"{response.status_code}"
        )

        return None, None

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    # HTTP 200でもXenForoのエラーが
    # 返ってくる場合がある。
    page_text = soup.get_text(
        " ",
        strip=True,
    )

    error_patterns = [
        "Oops! We ran into some problems",
        "The search could not be completed",
        "Please enter a search term",
        "The submitted form was invalid",
    ]

    for pattern in error_patterns:

        if (
            pattern.lower()
            in page_text.lower()
        ):

            print(
                "[Forum Vault] "
                f"Search rejected: "
                f"'{keyword}'"
            )

            return None, None

    return (
        response.text,
        response.url,
    )


# ==========================================
# Pagination
# ==========================================

def get_next_page_url(
    soup,
    current_url,
):
    """
    HTML内から確認できる次ページURLだけを返す。

    page=2等を推測してURLを生成しない。
    """

    # rel=next
    link = soup.find(
        "a",
        rel=lambda value: (
            value
            and (
                "next" in value
                if isinstance(value, list)
                else "next" in str(value)
            )
        ),
    )

    if link:

        href = link.get(
            "href"
        )

        if href:

            return urljoin(
                current_url,
                href,
            )

    # XenForo標準
    selectors = [
        "a.pageNav-jump--next",
        "a.pageNav-jump",
    ]

    for selector in selectors:

        link = soup.select_one(
            selector
        )

        if link:

            href = link.get(
                "href"
            )

            if href:

                return urljoin(
                    current_url,
                    href,
                )

    # pageNav-page内で、
    # 現在ページより大きいページ番号が
    # HTML上に存在する場合
    current_page = 1

    match = re.search(
        r"[?&]page=(\d+)",
        current_url,
    )

    if match:
        current_page = int(
            match.group(1)
        )

    candidates = []

    for link in soup.select(
        "li.pageNav-page a"
    ):

        href = link.get(
            "href",
            "",
        )

        match = re.search(
            r"[?&]page=(\d+)",
            href,
        )

        if not match:
            continue

        page_number = int(
            match.group(1)
        )

        if page_number > current_page:

            candidates.append(
                (
                    page_number,
                    href,
                )
            )

    if candidates:

        candidates.sort(
            key=lambda x: x[0]
        )

        return urljoin(
            current_url,
            candidates[0][1],
        )

    return None


# ==========================================
# Classification
# ==========================================

def classify_engine(
    title,
    description="",
):
    """
    スレッドのRPG Maker世代を推定する。
    """

    text = (
        f"{title} {description}"
    ).lower()

    if "rpg maker mz" in text:
        return "RPG Maker MZ"

    if "rpg maker mv" in text:
        return "RPG Maker MV"

    if "rpg maker vx ace" in text:
        return "RPG Maker VX Ace"

    if "rpg maker vx" in text:
        return "RPG Maker VX"

    if "rpg maker xp" in text:
        return "RPG Maker XP"

    if "rpg maker 2003" in text:
        return "RPG Maker 2003"

    if "rpg maker 2000" in text:
        return "RPG Maker 2000"

    if "rpg maker 95" in text:
        return "RPG Maker 95"

    if "rpg maker u2u" in text:
        return "RPG Maker U2U"

    return "unknown"


def classify_topic(
    title,
    description="",
):
    """
    Forumスレッドの大まかなテーマを推定する。
    """

    text = (
        f"{title} {description}"
    ).lower()

    if any(
        keyword in text
        for keyword in [
            "plugin",
            "plugins",
            "script",
        ]
    ):
        return "Forumプラグイン"

    if any(
        keyword in text
        for keyword in [
            "resource",
            "resources",
            "tileset",
            "sprite",
            "sprites",
            "asset",
            "assets",
        ]
    ):
        return "Forum素材"

    if any(
        keyword in text
        for keyword in [
            "tutorial",
            "how to",
            "guide",
        ]
    ):
        return "Forumチュートリアル"

    if any(
        keyword in text
        for keyword in [
            "question",
            "help",
            "problem",
            "issue",
        ]
    ):
        return "Forum質問"

    return "Forumその他"


# ==========================================
# Search Result Extraction
# ==========================================

def extract_search_results(
    html,
    search_url,
):
    """
    検索結果ページからスレッド情報を抽出する。
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    results = []
    seen_urls = set()

    containers = soup.select(
        ".block--messages, "
        ".block-body, "
        ".searchResults, "
        ".contentRow"
    )

    # 検索結果コンテナが見つからない場合は
    # ページ全体からthreads URLを探す。
    if not containers:
        containers = [soup]

    for container in containers:

        for link in container.select(
            "a[href]"
        ):

            href = link.get(
                "href"
            )

            if not href:
                continue

            url = normalize_url(
                href
            )

            if not is_thread_url(
                url
            ):
                continue

            if url in seen_urls:
                continue

            # Forum Vault自身などを除外
            if (
                "/forum-vault/" in url
            ):
                continue

            title = link.get_text(
                " ",
                strip=True,
            )

            # 検索結果によってはリンク文字列が
            # 空の場合があるため、親要素から補完する。
            if not title:

                parent = link.parent

                if parent:
                    title = parent.get_text(
                        " ",
                        strip=True,
                    )

            if not title:
                title = "Untitled"

            item = {
                "url": url,
                "title": title,
                "source": "RPG Maker Web Forum",
                "category": classify_topic(
                    title,
                    "",
                ),
                "engine": classify_engine(
                    title,
                    "",
                ),
                "language": "英語",
                "search_url": search_url,
                "vault_collected_at": (
                    datetime.now().astimezone()
                    .isoformat()
                ),
            }

            results.append(
                item
            )

            seen_urls.add(
                url
            )

    return results


# ==========================================
# Collection
# ==========================================

def collect():
    """
    Forum Vaultの収集を実行する。
    """

    progress = load_progress()
    index = load_index()

    # --------------------------------------
    # 既存indexの正規化
    # --------------------------------------

    (
        index,
        normalized_count,
        duplicate_count,
    ) = normalize_existing_index(
        index
    )

    print(
        "[Forum Vault] "
        f"Existing index normalized: "
        f"{normalized_count}"
    )

    print(
        "[Forum Vault] "
        f"Duplicate records removed: "
        f"{duplicate_count}"
    )

    # 正規化結果をすぐ保存
    # 検索途中でActionが失敗しても、
    # 既存データのURL整理自体は失わない。
    save_index(index)

    existing_urls = {
        item.get("url")
        for item in index
        if isinstance(item, dict)
        and item.get("url")
    }

    older_than = progress.get(
        "older_than"
    )

    keyword_index = int(
        progress.get(
            "keyword_index",
            0,
        )
    )

    print(
        "[Forum Vault] "
        f"older_than={older_than}"
    )

    print(
        "[Forum Vault] "
        f"keyword_index={keyword_index}"
    )

    session = create_session()

    added_count = 0

    processed_keywords = 0

    while (
        keyword_index
        < len(SEARCH_KEYWORDS)
        and processed_keywords
        < SEARCH_KEYWORDS_PER_RUN
    ):

        keyword = SEARCH_KEYWORDS[
            keyword_index
        ]

        print(
            "[Forum Vault] "
            f"Keyword "
            f"{keyword_index + 1}/"
            f"{len(SEARCH_KEYWORDS)}: "
            f"{keyword}"
        )

        current_url = None
        keyword_failed = False

        for page_number in range(
            1,
            SEARCH_PAGES_PER_KEYWORD + 1,
        ):

            print(
                "[Forum Vault]   "
                f"Page {page_number}"
            )

            if page_number == 1:

                html, search_url = search_forum(
                    session,
                    keyword,
                    older_than,
                )

                if html is None:
                    keyword_failed = True
                    break

                current_url = search_url

            else:

                if not current_url:
                    break

                try:

                    response = session.get(
                        current_url,
                        timeout=REQUEST_TIMEOUT,
                    )

                    response.raise_for_status()

                except requests.RequestException as e:

                    print(
                        "[Forum Vault]   "
                        f"Page request error: {e}"
                    )

                    keyword_failed = True
                    break

                html = response.text
                current_url = response.url

            results = extract_search_results(
                html,
                current_url,
            )

            print(
                "[Forum Vault]   "
                f"Candidates: {len(results)}"
            )

            for item in results:

                url = item.get(
                    "url"
                )

                if not url:
                    continue

                if url in existing_urls:
                    continue

                index.append(
                    item
                )

                existing_urls.add(
                    url
                )

                added_count += 1

            soup = BeautifulSoup(
                html,
                "html.parser",
            )

            next_url = get_next_page_url(
                soup,
                current_url,
            )

            if not next_url:
                break

            current_url = next_url

        if keyword_failed:

            print(
                "[Forum Vault] "
                f"Keyword failed: {keyword}"
            )

            print(
                "[Forum Vault] "
                "Progress will not advance "
                "for this keyword."
            )

            break

        keyword_index += 1
        processed_keywords += 1

    # --------------------------------------
    # キーワード完了処理
    # --------------------------------------

    if (
        not keyword_failed
        if "keyword_failed" in locals()
        else True
    ):

        if (
            keyword_index
            >= len(SEARCH_KEYWORDS)
        ):

            # 全キーワードを処理したら、
            # 次の30日前の期間へ進む。
            current_date = datetime.strptime(
                older_than,
                "%Y-%m-%d",
            ).date()

            next_older_than = (
                current_date
                - timedelta(days=30)
            ).isoformat()

            keyword_index = 0
            older_than = next_older_than

            print(
                "[Forum Vault] "
                "All keywords completed."
            )

    progress = {
        "older_than": older_than,
        "keyword_index": keyword_index,
        "completed": False,
    }

    save_index(index)
    save_progress(progress)

    print(
        "[Forum Vault] "
        f"Added: {added_count}"
    )

    print(
        "[Forum Vault] "
        f"Total index: {len(index)}"
    )

    print(
        "[Forum Vault] "
        f"Next keyword index: "
        f"{keyword_index}"
    )

    print(
        "[Forum Vault] "
        f"Next older_than: "
        f"{older_than}"
    )


# ==========================================
# Main
# ==========================================

if __name__ == "__main__":
    collect()
