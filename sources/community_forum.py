import json
from datetime import datetime, timedelta
from urllib.parse import urljoin

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
        "completed": False,
    }


def save_archive_progress(
    progress,
):

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


def get_previous_month(
    date_string,
):

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
# Forum Search
# ==========================================

def search_forum(older_than):
    """
    RPG Maker Web Forum の検索フォームを利用して、
    指定日より古い投稿を検索する。

    XenForo の検索では検索語が必須のため、
    "RPG Maker" を検索語として使用する。

    また、HTTP 200 でも検索エラー画面が返る場合があるため、
    HTML の内容を確認してから正常な検索結果として扱う。
    """

    search_page_url = urljoin(
        FORUM_URL,
        "/search/",
    )

    search_action_url = urljoin(
        FORUM_URL,
        "/search/search",
    )

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
        # 1. 検索フォームを GET
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

            for candidate in soup.find_all("form"):

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

            return None

        # ----------------------------------------
        # 2. hidden フィールドを取得
        # ----------------------------------------

        data = {}

        for input_tag in form.find_all("input"):

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

                value = input_tag.get(
                    "value",
                    "",
                )

                data[name] = value

        # ----------------------------------------
        # 3. 検索条件を設定
        # ----------------------------------------
        #
        # XenForo は検索語が空だと
        # "Please specify a search query..."
        # というエラーになる。
        #
        # まずは "RPG Maker" を検索語として使用する。
        #

        data.update(
            {
                "keywords": "RPG Maker",
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
            f"Posting search request: "
            f"keywords='RPG Maker', "
            f"older_than={older_than}"
        )

        # ----------------------------------------
        # 4. 同じ Session から POST
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
        # 5. HTMLを一時保存
        # ----------------------------------------

        with open(
            "forum_search_debug.html",
            "w",
            encoding="utf-8",
        ) as f:

            f.write(
                response.text
            )

        print(
            "[Forum Archive] "
            f"Search HTML saved: "
            f"{len(response.text)} bytes"
        )

        # ----------------------------------------
        # 6. HTTP 200でもエラー画面の場合がある
        # ----------------------------------------

        response_soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        page_title = (
            response_soup.title.get_text(
                " ",
                strip=True,
            )
            if response_soup.title
            else ""
        )

        page_text = response_soup.get_text(
            " ",
            strip=True,
        )

        search_error_messages = (
            "Please specify a search query",
            "Please specify a search query or the name of a member",
            "Oops! We ran into some problems",
        )

        for error_message in search_error_messages:

            if error_message.lower() in page_text.lower():

                print(
                    "[Forum Archive] "
                    "Search returned an error page: "
                    f"{error_message}"
                )

                print(
                    "[Forum Archive] "
                    f"Page title: {page_title}"
                )

                return None

        # ----------------------------------------
        # 7. 検索結果として返す
        # ----------------------------------------

        print(
            "[Forum Archive] "
            "Search page validation passed."
        )

        return response.text

    except requests.RequestException as e:

        print(
            "[Forum Archive] "
            f"Search request failed: {e}"
        )

        return None


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

    # ======================================
    # Search result links
    # ======================================

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
# Normal latest Forum
# ==========================================

def get_latest_items(
    seen,
):

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

def get_items(
    seen,
):

    global _pending_progress

    _pending_progress = None

    new_seen = list(
        seen
    )

    all_items = []

    # ======================================
    # ① Normal latest
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
    # ② Backfill progress
    # ======================================

    progress = load_archive_progress()

    completed = progress.get(
        "completed",
        False,
    )

    older_than = progress.get(
        "older_than"
    )

    if not older_than:

        older_than = (
            get_initial_older_than()
        )

    # ======================================
    # ③ Backfill
    # ======================================

    if completed:

        print(
            "[Forum Archive] "
            "Backfill already completed."
        )

    else:

        print(
            "[Forum Archive] "
            f"Searching older than: "
            f"{older_than}"
        )

        archive_index = (
            load_archive_index()
        )

        try:

            html = search_forum(
                older_than
            )

            # ----------------------------------
            # 検索そのものに失敗した場合
            # ----------------------------------
            #
            # ここでは絶対に進捗を進めない。
            #

            if html is None:

                print(
                    "[Forum Archive] "
                    "Search failed. "
                    "Progress will NOT advance."
                )

            else:

                candidates = (
                    extract_search_results(
                        html,
                        archive_index,
                    )
                )

                print(
                    "[Forum Archive] "
                    f"Candidates: "
                    f"{len(candidates)}"
                )

                for item in candidates:

                    print(
                        "[Forum Archive]"
                        "[Candidate] "
                        f"{item['title']}"
                    )

                    all_items.append(
                        item
                    )

                # ----------------------------------
                # 次回の検索位置
                # ----------------------------------
                #
                # 検索が正常に成立した場合のみ
                # 次の期間へ進める。
                #

                next_older_than = (
                    get_previous_month(
                        older_than
                    )
                )

                _pending_progress = {
                    "older_than": (
                        next_older_than
                    ),
                    "completed": False,
                }

                print(
                    "[Forum Archive] "
                    f"Next older_than: "
                    f"{next_older_than}"
                )

        except Exception as e:

            print(
                "[Forum Archive] "
                f"Search Error: {e}"
            )

            print(
                "[Forum Archive] "
                "Progress will NOT advance."
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
