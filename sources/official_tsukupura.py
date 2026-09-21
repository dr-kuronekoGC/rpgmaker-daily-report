# ==========================================
# ツクプラMZ
# ==========================================

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import (
    TSUKUPURA_URL,
    TSUKUPURA_SEEN_FILE,
)
from sources.base import get_html


SEEN_FILE = TSUKUPURA_SEEN_FILE

SOURCE_NAME = "ツクプラMZ"
MAX_PAGES = 3


def get_page_url(page):
    if page <= 1:
        return TSUKUPURA_URL

    return (
        f"{TSUKUPURA_URL.rstrip('/')}/page/{page}/"
    )


def extract_items(html):
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    items = []
    seen_urls = set()

    # WordPress系の一覧を想定。
    # 現在のサイトでは記事タイトルがh3内のリンクとして
    # 掲載されているため、まずそこを優先する。
    selectors = [
        "h3 a[href*='/archives/']",
        "h2 a[href*='/archives/']",
        "article h2 a[href*='/archives/']",
        "article h3 a[href*='/archives/']",
    ]

    links = []

    for selector in selectors:
        links = soup.select(selector)
        if links:
            break

    for link in links:
        title = link.get_text(
            " ",
            strip=True,
        )

        href = link.get(
            "href"
        )

        if not title or not href:
            continue

        url = urljoin(
            TSUKUPURA_URL,
            href,
        )

        if url in seen_urls:
            continue

        seen_urls.add(url)

        items.append(
            {
                "title": title,
                "url": url,
                "category": "ツクプラプラグイン",
                "source": SOURCE_NAME,
            }
        )

    return items


def get_items(seen):
    """
    ツクプラMZの新着プラグインを収集する。

    初回は現在の一覧をベースライン化し、
    過去の登録プラグインを一括掲載しない。
    """
    try:
        new_seen = list(seen)
        seen_set = set(seen)
        adopted_items = []

        for page in range(
            1,
            MAX_PAGES + 1,
        ):
            html = get_html(
                get_page_url(page)
            )

            page_items = extract_items(
                html
            )

            if not page_items:
                break

            for item in page_items:
                url = item["url"]

                if url in seen_set:
                    continue

                new_seen.append(url)
                seen_set.add(url)

                adopted_items.append(item)

        # 初回はベースライン。
        if not seen:
            print(
                f"[{SOURCE_NAME}] Baseline: "
                f"{len(new_seen)} items"
            )
            return [], new_seen

        print(
            f"[{SOURCE_NAME}] New: "
            f"{len(adopted_items)}"
        )

        return (
            adopted_items,
            new_seen,
        )

    except Exception as e:
        print(
            f"[{SOURCE_NAME}] Skip: {e}"
        )
        return [], seen
