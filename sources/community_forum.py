import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from categories import classify_forum
from config import (
    FORUM_SEEN_FILE,
    FORUM_URL,
)
from sources.base import get_html


SEEN_FILE = FORUM_SEEN_FILE

SOURCE_NAME = "RPG Maker Web Forum"
BASE_URL = "https://forums.rpgmakerweb.com"

# 通常の新着取得では、直近数ページを確認する。
# 既取得URLはseenで除外されるため、毎回同じ範囲を見てもよい。
MAX_PAGES = 10


def normalize_url(url):
    """
    ForumスレッドURLを正規化する。

    post/page/query/fragmentを除去して、
    スレッド単位のURLに統一する。
    """

    if not isinstance(url, str):
        return None

    url = url.strip()

    if not url:
        return None

    if url.startswith("/"):
        url = urljoin(BASE_URL, url)

    url = url.split("#", 1)[0]
    url = url.split("?", 1)[0]

    url = re.sub(
        r"/post-\d+/?$",
        "/",
        url,
        flags=re.IGNORECASE,
    )

    url = re.sub(
        r"/page-\d+/?$",
        "/",
        url,
        flags=re.IGNORECASE,
    )

    if "/threads/" not in url:
        return url

    return url.rstrip("/") + "/"


def is_thread_url(url):
    """
    RPG Maker Web ForumのスレッドURLか判定する。
    """

    if not isinstance(url, str):
        return False

    return "/threads/" in url


def get_title_link(container):
    """
    新着投稿ページからスレッドタイトルのリンクを取得する。

    XenForoの構造変更に備えて複数のselectorを試す。
    """

    selectors = [
        ".structItem-title a[href*='/threads/']",
        ".contentRow-title a[href*='/threads/']",
        "article a[href*='/threads/']",
    ]

    for selector in selectors:
        link = container.select_one(selector)

        if link is not None:
            return link

    return None


def extract_forum_name(container):
    """
    投稿カード周辺からForum名を取得する。

    取得できない場合は空文字を返す。
    """

    if container is None:
        return ""

    selectors = [
        "a[href*='/forums/']",
        ".node-title a",
        ".structItem-cell--meta a[href*='/forums/']",
    ]

    for selector in selectors:
        link = container.select_one(selector)

        if link is not None:
            text = link.get_text(
                " ",
                strip=True,
            )

            if text:
                return text

    return ""


def extract_items(html):
    """
    What's Newページから新着スレッドを抽出する。

    同じスレッドに複数の投稿がある場合も、
    スレッドURL単位で1件にまとめる。
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    items = []
    seen_urls = set()

    containers = soup.select(
        ".structItem, "
        ".contentRow, "
        "article.message--simple, "
        "article.message"
    )

    if not containers:
        containers = [soup]

    for container in containers:

        link = get_title_link(container)

        if link is None:
            continue

        raw_url = link.get("href")
        url = normalize_url(raw_url)

        if not is_thread_url(url):
            continue

        if url in seen_urls:
            continue

        title = link.get_text(
            " ",
            strip=True,
        )

        if not title:
            continue

        forum_name = extract_forum_name(
            container
        )

        category = classify_forum(
            title,
            forum_name,
        )

        if category is None:
            continue

        item = {
            "title": title,
            "url": url,
            "category": category,
            "source": SOURCE_NAME,
        }

        if forum_name:
            item["forum_name"] = forum_name

        items.append(item)
        seen_urls.add(url)

    return items


def get_next_page_url(html, current_url):
    """
    HTML内で明示的に確認できる次ページURLを返す。

    URLを推測してpage=2等を生成することはしない。
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    selectors = [
        "a[rel='next']",
        "a.pageNav-jump--next",
        "a.pageNav-jump",
    ]

    for selector in selectors:
        link = soup.select_one(selector)

        if link is None:
            continue

        href = link.get("href")

        if href:
            return urljoin(
                current_url,
                href,
            )

    return None


def get_items(seen):
    """
    RPG Maker Web Forumの新着情報を取得する。

    Forum Vaultの過去記事バックフィルは行わず、
    What's Newの通常取得だけを行う。
    """

    new_seen = list(seen)
    seen_set = set(seen)

    current_url = FORUM_URL
    adopted_items = []

    for page_number in range(
        1,
        MAX_PAGES + 1,
    ):

        try:
            html = get_html(current_url)

        except Exception as e:
            print(
                f"[{SOURCE_NAME}] "
                f"Page {page_number} error: {e}"
            )
            break

        page_items = extract_items(html)

        print(
            f"[{SOURCE_NAME}] "
            f"Page {page_number}: "
            f"{len(page_items)} adopted"
        )

        for item in page_items:

            url = item.get("url")

            if not url:
                continue

            if url in seen_set:
                continue

            new_seen.append(url)
            seen_set.add(url)

            adopted_items.append(item)

            print(
                f"[{SOURCE_NAME}]"
                f"[{item.get('category')}] "
                f"{item.get('title')}"
            )

        next_url = get_next_page_url(
            html,
            current_url,
        )

        if not next_url:
            break

        if next_url == current_url:
            break

        current_url = next_url

    print(
        f"[{SOURCE_NAME}] "
        f"New: {len(adopted_items)}"
    )

    return adopted_items, new_seen
