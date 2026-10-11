# ==========================================
# RPG Maker Web - International Resources Blog
# ==========================================

from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from config import (
    RPGMAKERWEB_BLOG_URL,
    RPGMAKERWEB_BLOG_SEEN_FILE,
)
from sources.base import get_html


SEEN_FILE = RPGMAKERWEB_BLOG_SEEN_FILE
SOURCE_NAME = "RPG Maker Web Blog"
ITEM_CATEGORY = "海外公式ブログ情報"

IGNORED_LINK_TITLES = {
    "read more",
    "learn more",
    "view more",
    "more",
    "next",
    "previous",
}


def normalize_article_url(url):
    """Return a stable URL for an article hosted on RPGMakerWeb."""
    if not isinstance(url, str) or not url.strip():
        return None

    absolute = urljoin(RPGMAKERWEB_BLOG_URL, url.strip())
    parts = urlsplit(absolute)

    if parts.netloc.lower() not in {
        "www.rpgmakerweb.com",
        "rpgmakerweb.com",
    }:
        return None

    if not parts.path.startswith("/blog/"):
        return None

    return urlunsplit((
        "https",
        "www.rpgmakerweb.com",
        parts.path.rstrip("/"),
        "",
        "",
    ))


def extract_blog_items(html, seen_urls=None):
    """Extract article links from the official English Resources listing."""
    seen_urls = set(seen_urls or [])
    soup = BeautifulSoup(html, "html.parser")
    items = []
    found_urls = set()

    for link in soup.select("a[href]"):
        url = normalize_article_url(link.get("href"))

        if not url or url in seen_urls or url in found_urls:
            continue

        title = link.get_text(" ", strip=True)

        if not title:
            image = link.select_one("img[alt]")
            if image:
                title = image.get("alt", "").strip()

        title = " ".join(title.split()).strip()

        if not title or title.lower() in IGNORED_LINK_TITLES:
            continue

        # A category listing may expose the same article through both its
        # image and title links. Keep one item per canonical article URL.
        found_urls.add(url)
        items.append({
            "title": title,
            "url": url,
            "category": ITEM_CATEGORY,
            "source": SOURCE_NAME,
        })

    return items


def get_items(seen):
    """Collect new English official resource/blog posts without a first-run flood."""
    if not isinstance(seen, list):
        seen = []

    try:
        html = get_html(RPGMAKERWEB_BLOG_URL)
        current_items = extract_blog_items(html)
        current_urls = [item["url"] for item in current_items]

        # Establish a baseline on the first successful run so old catalogue
        # entries do not all appear as fresh news in Slack.
        if not seen:
            print(
                f"[{SOURCE_NAME}] Baseline: {len(current_urls)} articles"
            )
            return [], current_urls

        seen_set = set(seen)
        new_seen = list(seen)
        adopted_items = []

        for item in current_items:
            url = item["url"]
            if url in seen_set:
                continue

            adopted_items.append(item)
            new_seen.append(url)
            seen_set.add(url)

        print(f"[{SOURCE_NAME}] New: {len(adopted_items)}")
        return adopted_items, new_seen

    except Exception as e:
        print(f"[{SOURCE_NAME}] Error: {e}")
        return [], seen
