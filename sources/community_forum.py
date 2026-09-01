import json
from datetime import datetime, timedelta
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import (
    FORUM_URL,
    FORUM_SEEN_FILE,
    FORUM_ARCHIVE_PROGRESS_FILE,
    FORUM_BACKFILL_PAGES_PER_RUN,
)

from categories import classify_forum
from sources.base import get_html
from archive import load_archive_index


SEEN_FILE = FORUM_SEEN_FILE


# ==========================================
# Backfill Progress
# ==========================================

_pending_progress = None


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

    # 初回は現在時刻から1か月前を開始地点にする
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

    # 31日ではなく、約1か月単位で戻す
    previous = current - timedelta(
        days=30
    )

    return previous.strftime(
        "%Y-%m-%d"
    )


# ==========================================
# Forum Search
# ==========================================

def build_search_url(
    older_than,
):

    base = urljoin(
        FORUM_URL,
        "search/search",
    )

    params = (
        f"?q="
        f"&o=date"
        f"&c%5Btitle_only%5D=0"
        f"&c%5Busers%5D="
        f"&c%5Bdate%5D="
        f"&c%5Bolder_than%5D={older_than}"
        f"&c%5Bnewer_than%5D="
    )

    return (
        base
        + params
    )


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
    # Thread links
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

        # Thread URLのみ
        if "/threads/" not in href:
            continue

        # 不要なURL
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

        # Archive済みなら除外
        if (
            href in archive_index
        ):
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
# Main collector
# ==========================================

def get_items(
    seen,
):

    global _pending_progress

    new_seen = seen.copy()

    all_items = []

    # ======================================
    # Progress
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
    # Archive index
    # ======================================

    archive_index = load_archive_index()

    # ======================================
    # ① 通常のForum新着
    # ======================================

    try:

        html = get_html(
            FORUM_URL
        )

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        latest_count = 0

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

            title = link.get_text(
                " ",
                strip=True,
            )

            if not title:
                continue

            if href in new_seen:

                continue

            category = classify_forum(
                title,
                "",
            )

            if category is None:

                continue

            item = {
                "title": title,
                "url": href,
                "category": category,
                "source": "Forum",
                "forum_backfill": False,
            }

            all_items.append(
                item
            )

            new_seen.append(
                href
            )

            latest_count += 1

            print(
                "[Forum][Latest]"
                f" [{category}] "
                f"{title}"
            )

        print(
            "[Forum] Latest new:",
            latest_count,
        )

    except Exception as e:

        print(
            "[Forum] Latest Error:",
            e,
        )

    # ======================================
    # ② Backfill
    # ======================================

    if completed:

        print(
            "[Forum Archive] "
            "Backfill already completed."
        )

    else:

        # ----------------------------------
        # 今回は1つの日付範囲だけ調査
        # ----------------------------------

        print(
            "[Forum Archive] "
            f"Searching older than: "
            f"{older_than}"
        )

        search_url = build_search_url(
            older_than
        )

        print(
            "[Forum Archive] "
            f"Search URL: {search_url}"
        )

        try:

            html = get_html(
                search_url
            )

            candidates = extract_search_results(
                html,
                archive_index,
            )

            print(
                "[Forum Archive] "
                f"Candidates: "
                f"{len(candidates)}"
            )

            for item in candidates:

                print(
                    "[Forum Archive][Candidate] "
                    f"{item['title']}"
                )

                all_items.append(
                    item
                )

            # ----------------------------------
            # 次回はさらに30日前へ
            # ----------------------------------

            next_older_than = (
                get_previous_month(
                    older_than
                )
            )

            _pending_progress = {
                "older_than": next_older_than,
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
        "[Forum] Backfill candidates:",
        backfill_count,
    )

    if _pending_progress:

        print(
            "[Forum Archive] "
            "Pending progress:",
            _pending_progress,
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