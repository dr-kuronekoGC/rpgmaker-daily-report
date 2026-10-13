# ==========================================
# itch.io Assets
# ==========================================

from datetime import datetime, timedelta, timezone

import requests

from bs4 import BeautifulSoup

from config import (
    ITCHIO_ASSET_RSS,
    ITCHIO_SEEN_FILE,
    REQUEST_TIMEOUT,
)

from sources.base import HEADERS

from categories.assets import classify_asset


SEEN_FILE = ITCHIO_SEEN_FILE

# itch.io has been returning HTTP 429 to automated requests.
# This collector only needs to discover new assets, so check it at most once
# every 24 hours rather than on every scheduled bot run.
MIN_FETCH_INTERVAL = timedelta(hours=24)
LAST_FETCH_PREFIX = "__itchio_last_successful_fetch_utc__="


ITCHIO_IGNORE_TITLES = (
    "assets",
    "albums & soundtracks",
    "upload your game assets",
)


def _get_last_successful_fetch(seen):
    """Return the persisted UTC timestamp, or None if no valid marker exists."""
    for value in seen:
        if not isinstance(value, str) or not value.startswith(LAST_FETCH_PREFIX):
            continue

        raw_timestamp = value[len(LAST_FETCH_PREFIX):]
        try:
            parsed = datetime.fromisoformat(raw_timestamp)
        except ValueError:
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)

    return None


def _should_skip_fetch(seen, now=None):
    """Avoid repeated requests to itch.io within the configured interval."""
    last_fetch = _get_last_successful_fetch(seen)
    if last_fetch is None:
        return False

    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)

    return now - last_fetch < MIN_FETCH_INTERVAL


def get_items(seen):

    if _should_skip_fetch(seen):
        print(
            "[itch.io a] Skipped: last successful check was less than "
            f"{MIN_FETCH_INTERVAL.total_seconds() / 3600:g} hours ago."
        )
        return [], seen

    response = requests.get(
        ITCHIO_ASSET_RSS,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    html = response.content.decode(
        "utf-8",
        errors="replace",
    )

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    adopted_items = []

    # Keep the timestamp marker out of URL deduplication.
    new_seen = [
        value
        for value in seen
        if not (
            isinstance(value, str)
            and value.startswith(LAST_FETCH_PREFIX)
        )
    ]

    seen_urls = set()

    for cell in soup.select(
        ".game_cell"
    ):

        title_tag = cell.select_one(
            ".game_title"
        )

        if not title_tag:
            continue

        title = title_tag.get_text(
            " ",
            strip=True,
        )

        if not title:
            continue

        if title.lower() in (
            ITCHIO_IGNORE_TITLES
        ):
            continue

        link = title_tag.find(
            "a"
        )

        if not link:
            continue

        href = link.get(
            "href"
        )

        if not href:
            continue

        if href.startswith("/"):
            href = (
                "https://itch.io"
                + href
            )

        if href in seen_urls:
            continue

        seen_urls.add(href)

        if href in new_seen:
            continue

        result = classify_asset(
            title,
            href,
        )

        if isinstance(result, tuple):

            category = result[0]
            tags = result[1]

        else:

            category = result
            tags = []

        if category is None:
            continue

        item = {
            "title": title,
            "url": href,
            "category": category,
            "source": "itch.io",
        }

        if tags:
            item["tags"] = tags

        adopted_items.append(
            item
        )

        new_seen.append(
            href
        )

        print(
            f"[itch.io a][{category}] {title}"
        )

    # The marker is only returned after a successful HTTP response and parse.
    # main.py persists it only when the Slack report is delivered successfully.
    new_seen.append(
        LAST_FETCH_PREFIX
        + datetime.now(timezone.utc).isoformat()
    )

    print(
        f"[itch.io a] New: "
        f"{len(adopted_items)}"
    )

    return (
        adopted_items,
        new_seen,
    )
