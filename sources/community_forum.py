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
# Forum Search Backfill
# ==========================================

def build_search_url():

    # Forumの検索ページ
    # まずは空検索で検索画面を取得し、
    # 実際の検索URL構造を確認する。
    return urljoin(
        FORUM_URL,
        "search/"
    )


def inspect_search_page(
    html,
):

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    print(
        "[Forum Search Debug] "
        "Inspecting search page..."
    )

    # ======================================
    # 基本情報
    # ======================================

    title_tag = soup.find(
        "title"
    )

    if title_tag:

        print(
            "[Forum Search Debug] "
            f"HTML title: "
            f"{title_tag.get_text(' ', strip=True)!r}"
        )

    print(
        "[Forum Search Debug] "
        f"HTML length: {len(html)}"
    )

    # ======================================
    # Search form
    # ======================================

    forms = soup.select(
        "form"
    )

    print(
        "[Forum Search Debug] "
        f"Forms: {len(forms)}"
    )

    for form in forms[:10]:

        action = form.get(
            "action"
        )

        method = form.get(
            "method"
        )

        classes = form.get(
            "class",
            []
        )

        print(
            "[Forum Search Form] "
            f"action={action!r} "
            f"method={method!r} "
            f"class={classes!r}"
        )

        # ----------------------------------
        # input
        # ----------------------------------

        for input_tag in form.select(
            "input"
        ):

            name = input_tag.get(
                "name"
            )

            input_type = input_tag.get(
                "type"
            )

            value = input_tag.get(
                "value"
            )

            placeholder = input_tag.get(
                "placeholder"
            )

            if (
                name
                or input_type
                or value
                or placeholder
            ):

                print(
                    "[Forum Search Input] "
                    f"name={name!r} "
                    f"type={input_type!r} "
                    f"value={value!r} "
                    f"placeholder={placeholder!r}"
                )

    # ======================================
    # Search related links
    # ======================================

    search_links = 0

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

        if (
            "/search" in href_lower
            or "search" in text_lower
            or "検索" in text
        ):

            full_url = urljoin(
                FORUM_URL,
                href,
            )

            print(
                "[Forum Search Link] "
                f"text={text!r} "
                f"url={full_url!r}"
            )

            search_links += 1

    print(
        "[Forum Search Debug] "
        f"Search links: {search_links}"
    )

    # ======================================
    # Search-related buttons
    # ======================================

    buttons = soup.select(
        "button, "
        "input[type='submit']"
    )

    print(
        "[Forum Search Debug] "
        f"Search buttons: {len(buttons)}"
    )

    for button in buttons[:20]:

        text = button.get_text(
            " ",
            strip=True,
        )

        name = button.get(
            "name"
        )

        value = button.get(
            "value"
        )

        button_type = button.get(
            "type"
        )

        print(
            "[Forum Search Button] "
            f"text={text!r} "
            f"name={name!r} "
            f"value={value!r} "
            f"type={button_type!r}"
        )

    # ======================================
    # ページネーション
    # ======================================

    pagination = soup.select(
        "a[href*='page'], "
        "a.pageNav-page, "
        "a.pageNav-jump, "
        "a[rel='next']"
    )

    print(
        "[Forum Search Debug] "
        f"Pagination candidates: "
        f"{len(pagination)}"
    )

    for link in pagination[:20]:

        href = link.get(
            "href"
        )

        text = link.get_text(
            " ",
            strip=True,
        )

        if href:

            print(
                "[Forum Search Pagination] "
                f"text={text!r} "
                f"href={href!r}"
            )


def run_search_diagnostic():

    search_url = build_search_url()

    print(
        "[Forum Search Debug] "
        f"Search URL: {search_url}"
    )

    try:

        html = get_html(
            search_url
        )

    except Exception as e:

        print(
            "[Forum Search Debug] "
            f"Search Error: {e}"
        )

        return

    inspect_search_page(
        html
    )

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
    
    # ======================================
    # Search diagnostic
    # ======================================

    run_search_diagnostic()

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