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

    XenForo の CSRF トークンとセッション Cookie が必要なため、
    検索フォームを GET して hidden フィールドを取得した後、
    同じ Session から POST する。
    """

    search_page_url = urljoin(FORUM_URL, "/search/")
    search_action_url = urljoin(FORUM_URL, "/search/search")

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

        soup = BeautifulSoup(response.text, "html.parser")

        form = soup.find(
            "form",
            attrs={
                "action": "/search/search",
            },
        )

        if form is None:
            # action の表記が異なる場合に備えて検索フォームを探す
            for candidate in soup.find_all("form"):
                action = candidate.get("action", "")
                if "/search/search" in action:
                    form = candidate
                    break

        if form is None:
            print("[Forum Archive] Search form not found.")
            return ""

        # ----------------------------------------
        # 2. hidden フィールドを取得
        # ----------------------------------------
        data = {}

        for input_tag in form.find_all("input"):
            name = input_tag.get("name")
            if not name:
                continue

            input_type = input_tag.get("type", "text")

            if input_type in ("hidden", "submit"):
                value = input_tag.get("value", "")
                data[name] = value

        # ----------------------------------------
        # 3. 検索条件を設定
        # ----------------------------------------
        data.update(
            {
                "keywords": "",
                "c[title_only]": "0",
                "c[users]": "",
                "c[newer_than]": "",
                "c[older_than]": older_than,
                "order": "date",
                "search_type": "post",
            }
        )

        # ----------------------------------------
        # 4. 同じ Session から POST
        # ----------------------------------------
        print(
            f"[Forum Archive] Posting search request: "
            f"older_than={older_than}"
        )

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
            f"[Forum Archive] Search response: "
            f"{response.status_code} {response.url}"
        )

        response.raise_for_status()

        return response.text

    except requests.RequestException as e:
        print(f"[Forum Archive] Search request failed: {e}")
        return ""

# ==========================================
# Search result extraction
# ==========================================

def extract_search_results(
    html,
    archive_index,
):

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
