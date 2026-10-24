import re
from urllib.parse import urljoin, urlsplit

from config import (
    OFFICIAL_NEWS_URL,
    OFFICIAL_SEEN_FILE,
)

from bs4 import BeautifulSoup

from categories import classify_official
from sources.html import get_html


SEEN_FILE = OFFICIAL_SEEN_FILE
ARTICLE_PATH_RE = re.compile(r"^/news/\d+/?$")
PUBLISHED_DATE_RE = re.compile(r"(?<!\d)(\d{4})[./年-](\d{1,2})[./月-](\d{1,2})日?")


def normalize_article_url(url):
    """Return a canonical URL only for individual official news articles."""
    if not isinstance(url, str) or not url.strip():
        return None

    absolute = urljoin(OFFICIAL_NEWS_URL, url.strip())
    parts = urlsplit(absolute)

    if parts.netloc.lower() not in {
        "rpgmakerofficial.com",
        "www.rpgmakerofficial.com",
    }:
        return None

    if not ARTICLE_PATH_RE.fullmatch(parts.path):
        return None

    return f"https://www.rpgmakerofficial.com{parts.path.rstrip('/')}/"


def _article_link_for_heading(tag):
    """Find an individual news URL near a heading without assuming one DOM shape."""
    for ancestor in [tag, *list(tag.parents)[:6]]:
        links = []
        if getattr(ancestor, "name", None) == "a":
            links.append(ancestor)
        links.extend(ancestor.select("a[href]") if hasattr(ancestor, "select") else [])

        for link in links:
            url = normalize_article_url(link.get("href"))
            if url:
                return url, ancestor

    return None, None


def _published_date(container):
    """Extract the site's visible YYYY.MM.DD publication date, if present."""
    if container is None:
        return None

    match = PUBLISHED_DATE_RE.search(container.get_text(" ", strip=True))
    if not match:
        return None

    year, month, day = (int(part) for part in match.groups())
    if not 1 <= month <= 12 or not 1 <= day <= 31:
        return None

    return f"{year:04d}.{month:02d}.{day:02d}"


def extract_official_news_items(html):
    """Extract individual official news URLs and visible publication dates."""
    soup = BeautifulSoup(html, "html.parser")
    items = []
    seen_urls = set()

    for tag in soup.find_all("h3"):
        title = tag.get_text(" ", strip=True)
        if not title:
            continue

        article_url, card = _article_link_for_heading(tag)
        if not article_url:
            # Do not invent an article URL if the page structure changes.
            continue
        if article_url in seen_urls:
            continue
        seen_urls.add(article_url)

        published_date = _published_date(card)
        item = {
            "title": title,
            "url": article_url,
            "category": classify_official(title),
            "source": "RPG Maker Official",
        }
        if published_date:
            item["published_date"] = published_date
        items.append(item)

    return items


def get_items(seen):
    adopted_items = []
    new_seen = list(seen) if isinstance(seen, list) else []
    seen_values = set(new_seen)

    try:
        html = get_html(OFFICIAL_NEWS_URL)
        current_items = extract_official_news_items(html)

        for item in current_items:
            title = item["title"]
            url = item["url"]

            # Keep compatibility with historical title-based seen records,
            # while storing URLs for stable future deduplication.
            if title in seen_values or url in seen_values:
                continue

            new_seen.append(url)
            seen_values.add(url)

            category = item.get("category")
            if category is None:
                continue

            adopted_items.append(item)
            print(
                f"[Official][{category}] "
                f"{item.get('published_date', '日付不明')} "
                f"{title} ({url})"
            )

        print(f"[Official] New: {len(adopted_items)}")

    except Exception as e:
        print("[Official] Error:", e)

    return adopted_items, new_seen
