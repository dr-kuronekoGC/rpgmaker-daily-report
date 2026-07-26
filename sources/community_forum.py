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

        if "/threads/" not in href:
            continue

        if "/page-" in href:
            continue

        if "/post-" in href:
            continue

        if href.endswith("/latest"):
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

        #
        # ここから追加
        #

        forum_name = ""

        try:

            thread_html = get_html(href)

            thread = BeautifulSoup(
                thread_html,
                "html.parser",
            )

            breadcrumb = thread.select(
                "ul.p-breadcrumbs li"
            )

            for item in breadcrumb:

                text = item.get_text(
                    " ",
                    strip=True,
                )

                if (
                    "Resources" in text
                    or "Support" in text
                    or "Games" in text
                    or "Development" in text
                    or "Tools" in text
                ):

                    forum_name = text
                    break

        except Exception:

            pass

        #
        # ここまで追加
        #

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
