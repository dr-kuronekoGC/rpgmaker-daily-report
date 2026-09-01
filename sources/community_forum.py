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


SEEN_FILE = FORUM_SEEN_FILE


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
        "next_page": 2,
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
# Forum URL
# ==========================================

def build_page_url(
    page,
):

    if page <= 1:
        return FORUM_URL

    separator = "&" if "?" in FORUM_URL else "?"

    return (
        f"{FORUM_URL}"
        f"{separator}page={page}"
    )


# ==========================================
# Thread extraction
# ==========================================

def extract_threads(
    html,
    seen=None,
    ignore_seen=False,
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

        seen_urls.add(href)

        title = link.get_text(
            " ",
            strip=True,
        )

        if not title:
            continue

        all_threads.append(
            href
        )

        # ----------------------------------
        # 通常取得ではseenを確認
        #
        # Backfillではignore_seen=True
        # としてGlobal seenを無視する
        # ----------------------------------

        if (
            not ignore_seen
            and seen is not None
            and href in seen
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

    new_seen = seen.copy()

    all_items = []

    progress = load_archive_progress()

    next_page = progress.get(
        "next_page",
        2,
    )

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
            new_seen,
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

        for page in range(
            next_page,
            next_page
            + FORUM_BACKFILL_PAGES_PER_RUN,
        ):

            page_url = build_page_url(
                page
            )

            print(
                f"[Forum Archive] "
                f"Checking page {page}"
            )

            try:

                html = get_html(
                    page_url
                )

            except Exception as e:

                print(
                    f"[Forum Archive] "
                    f"Page {page} Error: {e}"
                )

                break

            (
                all_threads,
                items,
            ) = extract_threads(
                html,
                seen=None,
                ignore_seen=True,
            )

            print(
                f"[Forum Archive] "
                f"Page {page}: "
                f"{len(all_threads)} threads, "
                f"{len(items)} candidates"
            )

            # ==================================
            # ページ自体にThreadが存在しない
            # → 過去取得終了
            # ==================================

            if len(all_threads) == 0:

                print(
                    f"[Forum Archive] "
                    f"No threads found on page {page}. "
                    f"Backfill completed."
                )

                progress[
                    "completed"
                ] = True

                break

            # ==================================
            # Backfill記事を追加
            #
            # Global seenには追加しない。
            #
            # → Forum Archiveの記事は
            #    Slack / Archive側へ渡す
            # ==================================

            for item in items:

                all_items.append(
                    item
                )

            # ==================================
            # 次回の開始ページを更新
            # ==================================

            progress[
                "next_page"
            ] = page + 1

            save_archive_progress(
                progress
            )

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

    print(
        "[Forum Archive] "
        f"Next page: "
        f"{progress.get('next_page')}"
    )

    print(
        "[Forum Archive] "
        f"Completed: "
        f"{progress.get('completed')}"
    )

    return (
        all_items,
        new_seen,
    )
