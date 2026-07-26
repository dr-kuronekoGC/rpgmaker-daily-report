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

        if "/page-" in href:
            continue

        if "/post-" in href:
            continue

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

        # --------------------------
        # 所属フォーラム取得
        # --------------------------

        forum_name = ""

        forum_link = link.find_parent().find_next("a")

        if forum_link:

            forum_href = forum_link.get("href", "")

            if "/forums/" in forum_href:

                forum_name = forum_link.get_text(
                    " ",
                    strip=True,
                )

        # --------------------------

        category = classify_forum(
            title,
            forum_name,
        )

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
