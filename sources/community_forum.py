from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import (
    FORUM_URL,
    FORUM_SEEN_FILE,
)

from categories import classify_forum
from sources.base import get_html


SEEN_FILE = FORUM_SEEN_FILE


def get_items(seen):

    html = get_html(FORUM_URL)

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    adopted_items = []

    new_seen = seen.copy()

    seen_urls = set()

    for link in soup.select("a[href]"):

        href = link.get("href")

        if not href:
            continue

        href = urljoin(
            FORUM_URL,
            href,
        )

        # --------------------------
        # Forum記事のみ取得
        # --------------------------

        if "/threads/" not in href:
            continue

        # ページ送り除外
        if "/page-" in href:
            continue

        # 投稿番号リンク除外
        if "/post-" in href:
            continue

        # latestリンク除外
        if href.endswith("/latest"):
            continue

        # --------------------------

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

        category = classify_forum(title)

        if category is None:
            continue

        new_seen.append(href)

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

    print(
        f"[Forum] New: {len(adopted_items)}"
    )

    return adopted_items, new_seen
