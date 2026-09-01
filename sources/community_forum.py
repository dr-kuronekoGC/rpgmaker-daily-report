from urllib.parse import urljoin, urlparse, parse_qs

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
# Forum進捗
# ==========================================

def load_archive_progress():

    try:

        with open(
            FORUM_ARCHIVE_PROGRESS_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            import json

            data = json.load(f)

            if isinstance(data, dict):
                return data

    except (
        FileNotFoundError,
        json.JSONDecodeError,
    ):

        pass

    return {
        "next_page": 1,
        "completed": False,
    }


def save_archive_progress(
    progress,
):

    import json

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
# Forum名取得
# ==========================================

def get_forum_name(
    url,
):

    try:

        html = get_html(url)

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        breadcrumb = soup.select(
            "ul.p-breadcrumbs li"
        )

        for item in breadcrumb:

            text = item.get_text(
                " ",
                strip=True,
            )

            if any(

                keyword in text

                for keyword in (

                    "Resources",
                    "Support",
                    "Games",
                    "Development",
                    "Tools",

                )

            ):

                return text

    except Exception:

        pass

    return ""


# ==========================================
# Thread extraction
# ==========================================

def extract_threads(
    html,
    seen,
):

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    adopted_items = []

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

        if href in seen:
            continue

        title = link.get_text(
            " ",
            strip=True,
        )

        if not title:
            continue

        forum_name = get_forum_name(
            href
        )

        category = classify_forum(
            title,
            forum_name,
        )

        if category is None:
            continue

        adopted_items.append(
            {
                "title": title,
                "url": href,
                "category": category,
                "source": "Forum",
            }
        )

        print(
            f"[Forum][{category}] {title}"
        )

    return adopted_items


# ==========================================
# Main
# ==========================================

def get_items(
    seen,
):

    new_seen = seen.copy()

    all_items = []

    # ======================================
    # Progress
    # ======================================

    progress = load_archive_progress()

    next_page = progress.get(
        "next_page",
        1,
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

        items = extract_threads(
            html,
            new_seen,
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

    except Exception as e:

        print(
            f"[Forum] Latest Error: {e}"
        )

    # ======================================
    # ② 過去アーカイブ
    # ======================================

    if not completed:

        pages_processed = 0

        for page in range(
            next_page,
            next_page
            + FORUM_BACKFILL_PAGES_PER_RUN,
        ):

            # page 1は最新ページと重なるため
            # Backfillではスキップする。

            if page <= 1:
                continue

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

            items = extract_threads(
                html,
                new_seen,
            )

            # ----------------------------------
            # ページにThreadが存在しない
            # → 過去ページ終了
            # ----------------------------------

            if not items:

                print(
                    f"[Forum Archive] "
                    f"No new items on page {page}"
                )

            else:

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

            pages_processed += 1

            progress[
                "next_page"
            ] = page + 1

        # ==================================
        # 完了判定
        # ==================================

        if pages_processed == 0:

            progress[
                "completed"
            ] = True

        save_archive_progress(
            progress
        )

    # ======================================
    # Result
    # ======================================

    print(
        f"[Forum] New: {len(all_items)}"
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
