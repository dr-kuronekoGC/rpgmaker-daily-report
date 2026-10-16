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

from sources.base import HEADERS, tracked_get

from categories.assets import classify_asset


SEEN_FILE = ITCHIO_SEEN_FILE

# itch.io has been returning HTTP 429 to automated requests.
# This collector only needs to discover new assets, so check it at most once
# every 24 hours rather than on every scheduled bot run.
MIN_FETCH_INTERVAL = timedelta(hours=24)
LAST_FETCH_PREFIX = "__itchio_last_attempt_utc__="


ITCHIO_IGNORE_TITLES = (
    "assets",
    "albums & soundtracks",
    "upload your game assets",
)


def _get_last_attempt(seen):
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
    last_attempt = _get_last_attempt(seen)
    if last_attempt is None:
        return False

    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)

    return now - last_attempt < MIN_FETCH_INTERVAL


def get_items(seen):

    if _should_skip_fetch(seen):
        print(
            "[itch.io a] Skipped: last request attempt was less than "
            f"{MIN_FETCH_INTERVAL.total_seconds() / 3600:g} hours ago."
        )
        return [], seen

    response = tracked_get(
        ITCHIO_ASSET_RSS,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )

    if response.status_code == 429:
        # Respect the site's rate limit and avoid retrying on the next scheduled run.
        new_seen = [
            value
            for value in seen
            if not (
                isinstance(value, str)
                and value.startswith(LAST_FETCH_PREFIX)
            )
        ]
        new_seen.append(
            LAST_FETCH_PREFIX
            + datetime.now(timezone.utc).isoformat()
        )
        global LAST_RUN_SUMMARY
        LAST_RUN_SUMMARY = {
            "checked": 1,
            "updated": 0,
            "baseline": 0,
            "unchanged": 0,
            "failed": 1,
        }
        print(
            "[itch.io a] HTTP 429 rate limit; will wait at least "
            f"{MIN_FETCH_INTERVAL.total_seconds() / 3600:g} hours before retrying."
        )
        return [], new_seen

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

    # Record the attempt after a successful response and parse.
    # main.py persists it only when the Slack report is delivered successfully.
    new_seen.append(
        LAST_FETCH_PREFIX
        + datetime.now(timezone.utc).isoformat()
    )

    LAST_RUN_SUMMARY = None

    print(
        f"[itch.io a] New: "
        f"{len(adopted_items)}"
    )

    return (
        adopted_items,
        new_seen,
    )
