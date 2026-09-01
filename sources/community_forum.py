import json

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
# Slack成功後に確定するProgress
# ==========================================

_pending_progress = None


# ==========================================
# Forum Archive Progress
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
        "next_url": None,
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
# Pagination
# ==========================================

def get_next_page_url(
    html,
):

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    print(
        "[Forum Archive] "
        "Searching pagination links..."
    )

    # --------------------------------------
    # pageNav周辺のリンクを全部確認
    # --------------------------------------

    for link in soup.select(
        "a[href]"
    ):

        href = link.get(
            "href"
        )

        text = link.get_text(
            " ",
            strip=True,
        )

        if not href:
            continue

        href_lower = href.lower()
        text_lower = text.lower()

        # ページネーションらしいリンクだけ表示
        if (
            "page" in href_lower
            or text_lower in (
                "next",
                "次へ",
                "次",
                ">",
                "»",
            )
        ):

            full_url = urljoin(
                FORUM_URL,
                href,
            )

            print(
                "[Forum Pagination] "
                f"text={text!r} "
                f"href={href!r} "
                f"url={full_url!r}"
            )

    # --------------------------------------
    # 既知のnextセレクタ
    # --------------------------------------

    selectors = [
        "a.pageNav-jump--next",
        "a[rel='next']",
        "a.pageNav-page--next",
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

                next_url = urljoin(
                    FORUM_URL,
                    href,
                )

                print(
                    "[Forum Pagination] "
                    f"Selected: {next_url}"
                )

                return next_url

    print(
        "[Forum Archive] "
        "No next page selector matched."
    )

    return None


# ==========================================
# Thread extraction
# ==========================================

def extract_threads(
    html,
    seen=None,
    ignore_seen=False,
    archive_index=None,
):

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    all_threads = []

    new_items = []

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

        title = link.get_text(
            " ",
            strip=True,
        )

        if not title:
            continue

        all_threads.append(
            href
        )

        # ==================================
        # 通常取得
        # ==================================

        if (
            not ignore_seen
            and seen is not None
            and href in seen
        ):
            continue

        # ==================================
        # Backfill
        #
        # Archiveに既にあるものは除外
        # Global seenは見ない
        # ==================================

        if ignore_seen:

            if (
                archive_index is not None
                and href in archive_index
            ):
                continue

        category = classify_forum(
            title,
            "",
        )

        if category is None:
            continue

        new_items.append(
            {
                "title": title,
                "url": href,
                "category": category,
                "source": "Forum",
                "forum_backfill": ignore_seen,
            }
        )

        print(
            f"[Forum][{category}] {title}"
        )

    return (
        all_threads,
        new_items,
    )


# ==========================================
# Main
# ==========================================

def get_items(
    seen,
):

    global _pending_progress

    new_seen = seen.copy()

    all_items = []

    progress = load_archive_progress()

    completed = progress.get(
        "completed",
        False,
    )

    # ======================================
    # ① 最新情報
    # ======================================

    try:

        html = get_html(
            FORUM_URL
        )

        (
            all_threads,
            items,
        ) = extract_threads(
            html,
            seen=new_seen,
            ignore_seen=False,
        )

        for item in items:

            url = item.get(
                "url"
            )

            if url:

                new_seen.append(
                    url
                )

            all_items.append(
                item
            )

        print(
            f"[Forum] Latest threads: "
            f"{len(all_threads)}"
        )

        print(
            f"[Forum] Latest new: "
            f"{len(items)}"
        )

    except Exception as e:

        print(
            f"[Forum] Latest Error: {e}"
        )

    # ======================================
    # ② 過去アーカイブ
    # ======================================

    if not completed:

        archive_index = load_archive_index()

        current_url = progress.get(
            "next_url"
        )

        # 初回は最新ページの次ページを取得
        if not current_url:

            try:

                latest_html = get_html(
                    FORUM_URL
                )

                current_url = get_next_page_url(
                    latest_html
                )

                if current_url:

                    print(
                        "[Forum Archive] "
                        "Initial next URL:",
                        current_url,
                    )

                else:

                    print(
                        "[Forum Archive] "
                        "Next page not found."
                    )

            except Exception as e:

                print(
                    "[Forum Archive] "
                    f"Initial pagination error: {e}"
                )

        pages_processed = 0

        next_url = current_url

        for _ in range(
            FORUM_BACKFILL_PAGES_PER_RUN
        ):

            if not next_url:
                break

            print(
                "[Forum Archive] "
                f"Checking: {next_url}"
            )

            try:

                html = get_html(
                    next_url
                )

            except Exception as e:

                print(
                    "[Forum Archive] "
                    f"Page Error: {e}"
                )

                break

            (
                all_threads,
                items,
            ) = extract_threads(
                html,
                seen=None,
                ignore_seen=True,
                archive_index=archive_index,
            )

            print(
                "[Forum Archive] "
                f"{len(all_threads)} threads, "
                f"{len(items)} new candidates"
            )

            # ==================================
            # Backfill記事
            # ==================================

            for item in items:

                all_items.append(
                    item
                )

            # ==================================
            # 次ページURL
            # ==================================

            next_page_url = get_next_page_url(
                html
            )

            pages_processed += 1

            if not next_page_url:

                print(
                    "[Forum Archive] "
                    "No next page. "
                    "Backfill completed."
                )

                _pending_progress = {
                    "next_url": None,
                    "completed": True,
                }

                break

            next_url = next_page_url

            _pending_progress = {
                "next_url": next_url,
                "completed": False,
            }

        if pages_processed > 0:

            if _pending_progress is None:

                _pending_progress = {
                    "next_url": next_url,
                    "completed": False,
                }

    # ======================================
    # Debug
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
        f"[Forum] New: "
        f"{len(all_items)}"
    )

    print(
        f"[Forum] Backfill candidates: "
        f"{backfill_count}"
    )

    if _pending_progress:

        print(
            "[Forum Archive] "
            "Pending progress:",
            _pending_progress,
        )

    else:

        print(
            "[Forum Archive] "
            "No progress update."
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
        "Progress saved after successful Slack delivery."
    )

    _pending_progress = None