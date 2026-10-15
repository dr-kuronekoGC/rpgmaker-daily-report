# ==========================================
# VisuStella
# ==========================================

from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import (
    VISUSTELLA_URL,
    VISUSTELLA_SEEN_FILE,
)

from sources.base import get_html


SEEN_FILE = VISUSTELLA_SEEN_FILE

# The site is hosted on itch.io and can return HTTP 429 to frequent requests.
# This collector only needs new listings, so check it at most once every 24 hours.
MIN_FETCH_INTERVAL = timedelta(hours=24)
LAST_FETCH_PREFIX = "__visustella_last_attempt_utc__="
LAST_RUN_SUMMARY = None


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
    """Avoid repeated requests to VisuStella within the configured interval."""
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


def _with_attempt_timestamp(seen):
    """Return seen state with a fresh timestamp marker, preserving saved URLs."""
    new_seen = [
        value for value in seen
        if not (
            isinstance(value, str)
            and value.startswith(LAST_FETCH_PREFIX)
        )
    ]
    new_seen.append(
        LAST_FETCH_PREFIX + datetime.now(timezone.utc).isoformat()
    )
    return new_seen


# ==========================================
# Plugin判定
# ==========================================

def normalize_visustella_url(url):
    """VisuStellaのURL表記を正規化する。"""

    if not isinstance(url, str):
        return None

    url = url.strip()

    if not url:
        return None

    url = url.split("#", 1)[0]
    url = url.split("?", 1)[0]
    url = url.rstrip("/")

    return url


def classify_visustella(title, url=""):

    normalized = title.lower().strip()

    # --------------------------------------
    # RPG Maker MZ Plugin
    # --------------------------------------

    if "plugin" in normalized:
        return "VisuStellaプラグイン"

    return None


# ==========================================
# Main
# ==========================================

def get_items(seen):

    global LAST_RUN_SUMMARY

    if not isinstance(seen, list):
        seen = []

    if _should_skip_fetch(seen):
        LAST_RUN_SUMMARY = None
        print(
            "[VisuStella] Skipped: last request attempt was less than "
            f"{MIN_FETCH_INTERVAL.total_seconds() / 3600:g} hours ago."
        )
        return [], seen

    try:
        html = get_html(VISUSTELLA_URL)

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        adopted_items = []

        # Keep the timestamp marker out of URL deduplication.
        new_seen = [
            value for value in seen
            if not (
                isinstance(value, str)
                and value.startswith(LAST_FETCH_PREFIX)
            )
        ]

        seen_urls = set()

        # ----------------------------------
        # itch.ioの商品カード
        # ----------------------------------

        game_cells = soup.select(".game_cell")

        for cell in game_cells:
            link = cell.select_one("a[href]")

            if not link:
                continue

            href = link.get("href")

            if not href:
                continue

            href = urljoin(VISUSTELLA_URL, href)
            href = normalize_visustella_url(href)

            if not href:
                continue

            # VisuStella以外へのリンクを除外
            if "visustellamz.itch.io/" not in href:
                continue

            # トップページ自身を除外
            if href == VISUSTELLA_URL.rstrip("/"):
                continue

            # 重複除外
            if href in seen_urls:
                continue

            seen_urls.add(href)

            # 既取得
            if href in new_seen:
                continue

            # --------------------------------
            # タイトル
            # --------------------------------

            title_tag = cell.select_one(".game_title")

            if title_tag:
                title = title_tag.get_text(" ", strip=True)
            else:
                title = link.get_text(" ", strip=True)

            if not title:
                continue

            # --------------------------------
            # 分類
            # --------------------------------

            category = classify_visustella(title, href)

            if category is None:
                continue

            # --------------------------------
            # 採用
            # --------------------------------

            new_seen.append(href)

            adopted_items.append({
                "title": title,
                "url": href,
                "category": category,
                "source": "VisuStella",
            })

        # Record every attempted request, including successful empty scans.
        new_seen = _with_attempt_timestamp(new_seen)
        LAST_RUN_SUMMARY = None

        print(f"[VisuStella] New: {len(adopted_items)}")

        return adopted_items, new_seen

    except Exception as exc:
        # Respect rate limits and avoid retrying an unavailable page every run.
        # main.py persists this marker only after successful Slack delivery.
        LAST_RUN_SUMMARY = {
            "checked": 1,
            "updated": 0,
            "baseline": 0,
            "unchanged": 0,
            "failed": 1,
        }
        print(f"[VisuStella] Error: {exc}")
        return [], _with_attempt_timestamp(seen)
