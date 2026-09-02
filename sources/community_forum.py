import json
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

import requests
from bs4 import BeautifulSoup

from config import (
    FORUM_URL,
    FORUM_SEEN_FILE,
    FORUM_ARCHIVE_PROGRESS_FILE,
)

from categories import classify_forum
from sources.base import get_html
from archive import load_archive_index


SEEN_FILE = FORUM_SEEN_FILE

_pending_progress = None


# ==========================================
# Forum Archive Search Settings
# ==========================================

# 1回のActionで処理する検索語数
SEARCH_KEYWORDS_PER_RUN = 3

# 1検索語あたり、1回のActionで処理する最大ページ数
SEARCH_PAGES_PER_KEYWORD = 3

# 検索語
#
# 「RPG Maker」だけでは拾えない記事を救出するため、
# 複数の検索語を順番に使用する。
#
SEARCH_KEYWORDS = [
    "RPG Maker",
    "RPG",
    "Maker",
    "MZ",
    "MV",
    "VX Ace",
    "XP",
    "plugin",
    "resource",
    "tileset",
    "sprite",
    "tutorial",
]


# ==========================================
# Archive Progress
# ==========================================

def load_archive_progress():

    try:

        with open(
            FORUM_ARCHIVE_PROGRESS_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            data = json.load(f)

            if isinstance(data, dict):
                return data

    except (
        FileNotFoundError,
        json.JSONDecodeError,
    ):
        pass

    return {
        "older_than": None,
        "keyword_index": 0,
        "completed": False,
    }


def save_archive_progress(progress):

    with open(
        FORUM_ARCHIVE_PROGRESS_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            progress,
            f,
            ensure_ascii=False,
            indent=2,
        )


# ==========================================
# Date handling
# ==========================================

def get_initial_older_than():

    return (
        datetime.now()
        - timedelta(days=30)
    ).strftime(
        "%Y-%m-%d"
    )


def get_previous_month(date_string):

    try:

        current = datetime.strptime(
            date_string,
            "%Y-%m-%d",
        )

    except ValueError:

        current = datetime.now()

    previous = (
        current
        - timedelta(days=30)
    )

    return previous.strftime(
        "%Y-%m-%d"
    )


# ==========================================
# Search URL helpers
# ==========================================

def get_next_page_url(
    html,
    current_url,
):
    """
    検索結果ページから次ページURLを取得する。

    XenForoのページネーション構造が変更されても
    できるだけ壊れにくいよう、rel=next と
    pagination 内のリンクを順番に確認する。
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    # ----------------------------------------
    # ① rel="next"
    # ----------------------------------------

    next_link = soup.find(
        "a",
        attrs={
            "rel": "next",
        },
    )

    if next_link:

        href = next_link.get(
            "href"
        )

        if href:

            return urljoin(
                current_url,
                href,
            )

    # ----------------------------------------
    # ② pagination の next link
    # ----------------------------------------

    for link in soup.select(
        "a.pageNav-jump--next, "
        "a.pageNav-jump, "
        "li.pageNav-page a"
    ):

        text = link.get_text(
            " ",
            strip=True,
        ).lower()

        aria = link.get(
            "aria-label",
            "",
        ).lower()

        title = link.get(
            "title",
            "",
        ).lower()

        if (
            "next" in text
            or "next" in aria
            or "next" in title
        ):

            href = link.get(
                "href"
            )

            if href:

                return urljoin(
                    current_url,
                    href,
                )

    # ----------------------------------------
    # ③ URLのpageパラメータを利用
    # ----------------------------------------

    parsed = urlparse(
        current_url
    )

    query = parse_qs(
        parsed.query
    )

    current_page = 1

    if "page" in query:

        try:
            current_page = int(
                query["page"][0]
            )
        except (
            ValueError,
            TypeError,
        ):
            current_page = 1

    next_page = (
        current_page + 1
    )

    query["page"] = [
        str(next_page)
    ]

    next_query = urlencode(
        query,
        doseq=True,
    )

    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            next_query,
            parsed.fragment,
        )
    )


# ==========================================
# Forum Search
# ==========================================

def search_forum(
    keyword,
    older_than,
    session=None,
):
    """
    RPG Maker Web Forum の検索フォームを利用して、
    指定キーワード・指定日以前の投稿を検索する。

    戻り値:
        (html, url)

    検索失敗時:
        (None, None)
    """

    search_page_url = urljoin(
        FORUM_URL,
        "/search/",
    )

    search_action_url = urljoin(
        FORUM_URL,
        "/search/search",
    )

    if session is None:

        session = requests.Session()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/151.0.0.0 Safari/537.36"
        )
    }

    try:

        # ----------------------------------------
        # 1. 検索フォーム GET
        # ----------------------------------------

        response = session.get(
            search_page_url,
            headers=headers,
            timeout=30,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        form = soup.find(
            "form",
            attrs={
                "action": "/search/search",
            },
        )

        if form is None:

            for candidate in soup.find_all(
                "form"
            ):

                action = candidate.get(
                    "action",
                    "",
                )

                if "/search/search" in action:

                    form = candidate
                    break

        if form is None:

            print(
                "[Forum Archive] "
                "Search form not found."
            )

            return None, None

        # ----------------------------------------
        # 2. hidden fields
        # ----------------------------------------

        data = {}

        for input_tag in form.find_all(
            "input"
        ):

            name = input_tag.get(
                "name"
            )

            if not name:
                continue

            input_type = input_tag.get(
                "type",
                "text",
            )

            if input_type in (
                "hidden",
                "submit",
            ):

                data[name] = input_tag.get(
                    "value",
                    "",
                )

        # ----------------------------------------
        # 3. 検索条件
        # ----------------------------------------

        data.update(
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

        print(
            "[Forum Archive] "
            f"Searching keyword='{keyword}', "
            f"older_than={older_than}"
        )

        # ----------------------------------------
        # 4. POST
        # ----------------------------------------

        response = session.post(
            search_action_url,
            data=data,
            headers={
                **headers,
                "Referer": search_page_url,
            },
            timeout=30,
        )

        print(
            "[Forum Archive] "
            f"Search response: "
            f"{response.status_code} "
            f"{response.url}"
        )

        response.raise_for_status()

        # ----------------------------------------
        # 5. Debug HTML
        # ----------------------------------------

        with open(
            "forum_search_debug.html",
            "w",
            encoding="utf-8",
        ) as f:

            f.write(
                response.text
            )

        # ----------------------------------------
        # 6. HTTP 200でもエラーの場合がある
        # ----------------------------------------

        result_soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        page_title = (
            result_soup.title.get_text(
                " ",
                strip=True,
            )
            if result_soup.title
            else ""
        )

        page_text = result_soup.get_text(
            " ",
            strip=True,
        )

        error_messages = (
            "Please specify a search query",
            "Please specify a search query or the name of a member",
            "Oops! We ran into some problems",
        )

        for error_message in error_messages:

            if (
                error_message.lower()
                in page_text.lower()
            ):

                print(
                    "[Forum Archive] "
                    "Search returned an error page: "
                    f"{error_message}"
                )

                print(
                    "[Forum Archive] "
                    f"Page title: {page_title}"
                )

                return None, None

        print(
            "[Forum Archive] "
            "Search page validation passed."
        )

        return (
            response.text,
            response.url,
        )

    except requests.RequestException as e:

        print(
            "[Forum Archive] "
            f"Search request failed: {e}"
        )

        return None, None


# ==========================================
# Search result extraction
# ==========================================

def extract_search_results(
    html,
    archive_index,
):

    if not html:

        return []

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    items = []

    seen_urls = set()

    for link in soup.select(
        "a[href]"
    ):

        href = link.get(
            "href"
        )

        if not href:
            continue

        href = urljoin(
            FORUM_URL,
            href,
        )

        if "/threads/" not in href:
            continue

        if "/page-" in href:
            continue

        if "/post-" in href:
            continue

        if href.endswith(
            "/latest"
        ):
            continue

        if href in seen_urls:
            continue

        seen_urls.add(
            href
        )

        # ----------------------------------
        # Archive済み
        # ----------------------------------

        if href in archive_index:
            continue

        title = link.get_text(
            " ",
            strip=True,
        )

        if not title:
            continue

        category = classify_forum(
            title,
            "",
        )

        if category is None:
            continue

        items.append(
            {
                "title": title,
                "url": href,
                "category": category,
                "source": "Forum",
                "forum_backfill": True,
            }
        )

    return items


# ==========================================
# Latest Forum
# ==========================================

def get_latest_items(seen):

    items = []

    html = get_html(
        FORUM_URL
    )

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    local_seen = set()

    for link in soup.select(
        "a[href]"
    ):

        href = link.get(
            "href"
        )

        if not href:
            continue

        href = urljoin(
            FORUM_URL,
            href,
        )

        if "/threads/" not in href:
            continue

        if "/page-" in href:
            continue

        if "/post-" in href:
            continue

        if href.endswith(
            "/latest"
        ):
            continue

        if href in local_seen:
            continue

        local_seen.add(
            href
        )

        if href in seen:
            continue

        title = link.get_text(
            " ",
            strip=True,
        )

        if not title:
            continue

        category = classify_forum(
            title,
            "",
        )

        if category is None:
            continue

        items.append(
            {
                "title": title,
                "url": href,
                "category": category,
                "source": "Forum",
                "forum_backfill": False,
            }
        )

    return items


# ==========================================
# Main collector
# ==========================================

def get_items(seen):

    global _pending_progress

    _pending_progress = None

    new_seen = list(
        seen
    )

    all_items = []

    # ======================================
    # ① Latest
    # ======================================

    try:

        latest_items = get_latest_items(
            seen
        )

        all_items.extend(
            latest_items
        )

        for item in latest_items:

            new_seen.append(
                item["url"]
            )

        print(
            "[Forum] Latest new:",
            len(latest_items),
        )

    except Exception as e:

        print(
            "[Forum] Latest Error:",
            e,
        )

    # ======================================
    # ② Archive progress
    # ======================================

    progress = load_archive_progress()

    completed = progress.get(
        "completed",
        False,
    )

    older_than = progress.get(
        "older_than"
    )

    keyword_index = progress.get(
        "keyword_index",
        0,
    )

    if not older_than:

        older_than = (
            get_initial_older_than()
        )

    try:

        keyword_index = int(
            keyword_index
        )

    except (
        ValueError,
        TypeError,
    ):

        keyword_index = 0

    if keyword_index < 0:
        keyword_index = 0

    if keyword_index >= len(
        SEARCH_KEYWORDS
    ):

        keyword_index = 0

    # ======================================
    # ③ Already completed
    # ======================================

    if completed:

        print(
            "[Forum Archive] "
            "Backfill already completed."
        )

        return (
            all_items,
            new_seen,
        )

    # ======================================
    # ④ Search
    # ======================================

    archive_index = (
        load_archive_index()
    )

    session = requests.Session()

    processed_keywords = 0

    current_keyword_index = (
        keyword_index
    )

    progress_failed = False

    while (
        processed_keywords
        < SEARCH_KEYWORDS_PER_RUN
    ):

        if (
            current_keyword_index
            >= len(SEARCH_KEYWORDS)
        ):

            break

        keyword = SEARCH_KEYWORDS[
            current_keyword_index
        ]

        print(
            "[Forum Archive] "
            f"Keyword {current_keyword_index + 1}/"
            f"{len(SEARCH_KEYWORDS)}: "
            f"{keyword}"
        )

        html, search_url = search_forum(
            keyword,
            older_than,
            session=session,
        )

        if html is None:

            print(
                "[Forum Archive] "
                "Search failed. "
                "Progress will NOT advance."
            )

            progress_failed = True
            break

        # ----------------------------------
        # Search result page
        # ----------------------------------

        current_html = html
        current_url = search_url

        pages_processed = 0

        keyword_seen_urls = set()

        while (
            pages_processed
            < SEARCH_PAGES_PER_KEYWORD
        ):

            candidates = (
                extract_search_results(
                    current_html,
                    archive_index,
                )
            )

            added_count = 0

            for item in candidates:

                url = item[
                    "url"
                ]

                if url in keyword_seen_urls:
                    continue

                keyword_seen_urls.add(
                    url
                )

                all_items.append(
                    item
                )

                added_count += 1

                print(
                    "[Forum Archive]"
                    "[Candidate] "
                    f"{item['title']}"
                )

            print(
                "[Forum Archive] "
                f"Keyword='{keyword}' "
                f"page={pages_processed + 1} "
                f"candidates={added_count}"
            )

            pages_processed += 1

            # ----------------------------------
            # 次ページ
            # ----------------------------------

            next_url = (
                get_next_page_url(
                    current_html,
                    current_url,
                )
            )

            if not next_url:
                break

            if next_url == current_url:
                break

            # ----------------------------------
            # 次ページ GET
            # ----------------------------------

            try:

                response = session.get(
                    next_url,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 "
                            "(Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 "
                            "(KHTML, like Gecko) "
                            "Chrome/151.0.0.0 "
                            "Safari/537.36"
                        ),
                        "Referer": current_url,
                    },
                    timeout=30,
                )

                response.raise_for_status()

                current_html = (
                    response.text
                )

                current_url = (
                    response.url
                )

            except requests.RequestException as e:

                print(
                    "[Forum Archive] "
                    f"Next page request failed: {e}"
                )

                progress_failed = True
                break

        if progress_failed:
            break

        # ----------------------------------
        # 次の検索語へ
        # ----------------------------------

        current_keyword_index += 1
        processed_keywords += 1

    # ======================================
    # ⑤ Progress
    # ======================================

    if not progress_failed:

        # ----------------------------------
        # 全検索語を終了した場合
        # ----------------------------------

        if (
            current_keyword_index
            >= len(SEARCH_KEYWORDS)
        ):

            next_older_than = (
                get_previous_month(
                    older_than
                )
            )

            next_keyword_index = 0

            # ----------------------------------
            # ここでは「期間を一つ進める」
            # ----------------------------------

            _pending_progress = {
                "older_than": (
                    next_older_than
                ),
                "keyword_index": (
                    next_keyword_index
                ),
                "completed": False,
            }

            print(
                "[Forum Archive] "
                "All keywords completed."
            )

            print(
                "[Forum Archive] "
                f"Next older_than: "
                f"{next_older_than}"
            )

        else:

            # ----------------------------------
            # 今回処理した検索語まで保存
            # ----------------------------------

            _pending_progress = {
                "older_than": older_than,
                "keyword_index": (
                    current_keyword_index
                ),
                "completed": False,
            }

            print(
                "[Forum Archive] "
                "Next keyword index: "
                f"{current_keyword_index}"
            )

    # ======================================
    # Summary
    # ======================================

    backfill_count = sum(
        1
        for item in all_items
        if item.get(
            "forum_backfill",
            False,
        )
    )

    print(
        "[Forum] New:",
        len(all_items),
    )

    print(
        "[Forum] "
        "Backfill candidates:",
        backfill_count,
    )

    return (
        all_items,
        new_seen,
    )


# ==========================================
# Finalize
# ==========================================

def finalize():

    global _pending_progress

    if _pending_progress is None:
        return

    save_archive_progress(
        _pending_progress
    )

    print(
        "[Forum Archive] "
        "Progress saved after "
        "successful Slack delivery."
    )

    _pending_progress = None
