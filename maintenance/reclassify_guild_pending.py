# ==========================================
# Rebuild old RPG Maker Guild pending items
# ==========================================

import json
import re
import shutil
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


ROOT_DIR = (
    Path(__file__)
    .resolve()
    .parent.parent
)

sys.path.insert(
    0,
    str(ROOT_DIR),
)

from config import (
    GUILD_URL,
    PENDING_ITEMS_FILE,
    REQUEST_TIMEOUT,
)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(compatible; RPGMakerDailyReport/1.0)"
    )
}


GUILD_SOURCE = "RPG Maker Guild"


# ==========================================
# Guild Categories
# ==========================================

CATEGORY_URLS = {
    "プラグイン": (
        "https://guild.rpgmakerofficial.com/"
        "c/14-category/17-category/17"
    ),
    "素材": (
        "https://guild.rpgmakerofficial.com/"
        "c/14-category/20-category/20"
    ),
    "RGSSx": (
        "https://guild.rpgmakerofficial.com/"
        "c/14-category/21-category/21"
    ),
}


# ==========================================
# Settings
# ==========================================

# 1カテゴリにつき取得するページ数
MAX_PAGES = 3

# ページ間隔
REQUEST_INTERVAL = 1.5

# 429時の最大リトライ回数
MAX_RETRIES = 4

# Retry-Afterが取得できない場合
DEFAULT_RETRY_WAIT = 10


# ==========================================
# Sound Classification
# ==========================================

SOUND_KEYWORDS = [
    "bgm",
    "bgs",
    "音楽",
    "効果音",
    "サウンド",
    "音声",
    "se素材",
    "bgm素材",
    "音素材",
]


SOUND_PATTERNS = [
    r"\bbgm\b",
    r"\bbgs\b",
    r"\baudio\b",
    r"\bmusic\b",
    r"\bsfx\b",
    r"\bsound\b",
    r"\bsound effect\b",
    r"\bsound effects\b",
]


def classify_material(
    title,
    tags,
):
    """
    Guildの「素材」カテゴリを
    グラフィック / サウンドに分類する。

    サウンドと明確に判断できない場合は
    グラフィック素材とする。
    """

    text = " ".join(
        [title] + list(tags)
    ).lower()

    for keyword in SOUND_KEYWORDS:

        if keyword in text:
            return "サウンド素材"

    for pattern in SOUND_PATTERNS:

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            return "サウンド素材"

    return "グラフィック素材"


# ==========================================
# URL Helpers
# ==========================================

def normalize_url(url):
    """
    URL末尾のスラッシュを除去して比較しやすくする。
    """

    if not isinstance(
        url,
        str,
    ):
        return ""

    return url.strip().rstrip("/")


# ==========================================
# Page Fetch
# ==========================================

def get_page(
    session,
    url,
    page,
):
    """
    Guildカテゴリページを取得する。

    page=1はカテゴリURLそのもの。
    2以降は ?page=N を使用する。
    """

    if page == 1:

        page_url = url

    else:

        separator = (
            "&"
            if "?" in url
            else "?"
        )

        page_url = (
            f"{url}"
            f"{separator}"
            f"page={page}"
        )

    for attempt in range(
        MAX_RETRIES + 1
    ):

        try:

            response = session.get(
                page_url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )

            # ----------------------------------
            # Rate Limit
            # ----------------------------------

            if response.status_code == 429:

                if attempt >= MAX_RETRIES:
                    response.raise_for_status()

                retry_after = (
                    response.headers.get(
                        "Retry-After"
                    )
                )

                try:

                    wait_seconds = float(
                        retry_after
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    wait_seconds = (
                        DEFAULT_RETRY_WAIT
                    )

                wait_seconds = min(
                    max(
                        wait_seconds,
                        5,
                    ),
                    60,
                )

                print(
                    "[Guild cleanup] "
                    "429 Too Many Requests. "
                    f"Waiting "
                    f"{wait_seconds:.1f}s "
                    f"(retry "
                    f"{attempt + 1}/"
                    f"{MAX_RETRIES})"
                )

                time.sleep(
                    wait_seconds
                )

                continue

            response.raise_for_status()

            return response.text

        except requests.RequestException:

            if attempt >= MAX_RETRIES:
                raise

            wait_seconds = min(
                5 * (
                    2 ** attempt
                ),
                60,
            )

            print(
                "[Guild cleanup] "
                "Request error. "
                f"Waiting "
                f"{wait_seconds}s "
                "before retry."
            )

            time.sleep(
                wait_seconds
            )

    raise RuntimeError(
        "Unable to fetch Guild page"
    )


# ==========================================
# Topic Extraction
# ==========================================

def extract_topics(
    html,
):
    """
    Guildカテゴリ一覧から
    トピックを抽出する。

    戻り値:
        [
            {
                "url": ...,
                "title": ...,
                "tags": [...]
            }
        ]
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    items = []

    topic_rows = soup.select(
        "tr.topic-list-item"
    )

    for topic in topic_rows:

        link = topic.select_one(
            "a.title"
        )

        if link is None:
            continue

        href = link.get(
            "href"
        )

        title = link.get_text(
            " ",
            strip=True,
        )

        if not href or not title:
            continue

        url = urljoin(
            GUILD_URL,
            href,
        )

        if not re.search(
            r"/t/[^/]+/\d+",
            url,
        ):
            continue

        tags = []

        for tag in topic.select(
            ".discourse-tag"
        ):

            text = tag.get_text(
                " ",
                strip=True,
            )

            if not text:
                continue

            if text not in tags:
                tags.append(text)

        items.append(
            {
                "url": normalize_url(url),
                "title": title,
                "tags": tags,
            }
        )

    return items


# ==========================================
# Build Guild URL Map
# ==========================================

def build_guild_url_map(
    session,
):
    """
    Guildのカテゴリページから、

        URL -> Guildカテゴリ

    の対応表を作る。

    例:
        https://.../t/example/123
            -> プラグイン
    """

    url_map = {}

    for guild_category, category_url in (
        CATEGORY_URLS.items()
    ):

        print(
            "[Guild cleanup] "
            f"Fetching category: "
            f"{guild_category}"
        )

        category_count = 0

        for page in range(
            1,
            MAX_PAGES + 1,
        ):

            try:

                html = get_page(
                    session,
                    category_url,
                    page,
                )

            except Exception as e:

                print(
                    "[Guild cleanup] "
                    f"Page error "
                    f"({guild_category}, "
                    f"page {page}): {e}"
                )

                # 取得できないページがあっても、
                # それまで取得した情報は使用する。
                break

            topics = extract_topics(
                html
            )

            for topic in topics:

                url = topic["url"]

                if not url:
                    continue

                # 同じURLが複数カテゴリに
                # 存在する場合は上書きしない。
                if url in url_map:
                    continue

                url_map[url] = {
                    "guild_category": (
                        guild_category
                    ),
                    "title": topic["title"],
                    "tags": topic["tags"],
                }

                category_count += 1

            if page < MAX_PAGES:
                time.sleep(
                    REQUEST_INTERVAL
                )

        print(
            "[Guild cleanup] "
            f"{guild_category}: "
            f"{category_count} topics found"
        )

        time.sleep(
            REQUEST_INTERVAL
        )

    print(
        "[Guild cleanup] "
        f"Guild URL map: {len(url_map)} topics"
    )

    return url_map


# ==========================================
# Classification
# ==========================================

def classify_topic(
    guild_category,
    title,
    tags,
):
    """
    Guildカテゴリを
    Daily Reportカテゴリへ変換する。
    """

    if guild_category == "プラグイン":

        return "プラグイン"

    if guild_category == "RGSSx":

        return "プラグイン"

    if guild_category == "素材":

        return classify_material(
            title,
            tags,
        )

    return None


# ==========================================
# File Helpers
# ==========================================

def load_json(
    path,
):

    with path.open(
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)


def get_backup_path(
    pending_path,
):

    return pending_path.with_name(
        pending_path.name
        + ".guild_cleanup_backup"
    )


# ==========================================
# Main
# ==========================================

def main():

    pending_path = Path(
        PENDING_ITEMS_FILE
    )

    if not pending_path.exists():

        raise FileNotFoundError(
            "Pending file not found: "
            f"{pending_path}"
        )

    backup_path = get_backup_path(
        pending_path
    )

    if not backup_path.exists():

        raise FileNotFoundError(
            "Original Guild backup not found: "
            f"{backup_path}"
        )

    # --------------------------------------
    # Current pending
    # --------------------------------------

    current_items = load_json(
        pending_path
    )

    if not isinstance(
        current_items,
        list,
    ):

        raise ValueError(
            "pending_items.json "
            "is not a list"
        )

    # --------------------------------------
    # Original backup
    # --------------------------------------

    backup_items = load_json(
        backup_path
    )

    if not isinstance(
        backup_items,
        list,
    ):

        raise ValueError(
            "Guild cleanup backup "
            "is not a list"
        )

    # --------------------------------------
    # Safety backup
    # --------------------------------------

    safety_backup = pending_path.with_name(
        pending_path.name
        + ".guild_cleanup_before_retry"
    )

    shutil.copy2(
        pending_path,
        safety_backup,
    )

    # ======================================
    # Separate non-Guild items
    # ======================================

    non_guild_items = [
        item
        for item in current_items
        if item.get(
            "source"
        ) != GUILD_SOURCE
    ]

    # ======================================
    # Restore original Guild items
    # ======================================

    guild_items = [
        item
        for item in backup_items
        if item.get(
            "source"
        ) == GUILD_SOURCE
    ]

    print(
        "===== Guild Pending Rebuild ====="
    )

    print(
        "Guild items from backup: "
        f"{len(guild_items)}"
    )

    print(
        "Non-Guild items preserved: "
        f"{len(non_guild_items)}"
    )

    # ======================================
    # Build URL map
    # ======================================

    session = requests.Session()

    guild_url_map = build_guild_url_map(
        session
    )

    # ======================================
    # Process
    # ======================================

    updated_guild = []

    reclassified = 0
    unchanged = 0
    removed = 0
    unmatched = 0
    errors = 0

    for index, item in enumerate(
        guild_items,
        start=1,
    ):

        url = normalize_url(
            item.get(
                "url"
            )
        )

        title = item.get(
            "title",
            "",
        )

        print(
            f"[Guild cleanup] "
            f"{index}/{len(guild_items)} "
            f"{title}"
        )

        # ----------------------------------
        # URL missing
        # ----------------------------------

        if not url:

            errors += 1

            updated_guild.append(
                item
            )

            print(
                "[Guild cleanup] "
                "ERROR: Missing URL. "
                "Keeping item."
            )

            continue

        # ==================================
        # URL lookup
        # ==================================

        guild_info = guild_url_map.get(
            url
        )

        # ----------------------------------
        # Not found in current categories
        # ----------------------------------

        if guild_info is None:

            unmatched += 1

            updated_guild.append(
                item
            )

            print(
                "[Guild cleanup] "
                "URL not found in current "
                "Guild category pages. "
                "Keeping item."
            )

            continue

        # ----------------------------------
        # Guild category
        # ----------------------------------

        guild_category = guild_info[
            "guild_category"
        ]

        title_from_guild = guild_info[
            "title"
        ]

        tags = guild_info[
            "tags"
        ]

        new_category = classify_topic(
            guild_category,
            title_from_guild or title,
            tags,
        )

        # ----------------------------------
        # Unexpected category
        # ----------------------------------

        if new_category is None:

            errors += 1

            updated_guild.append(
                item
            )

            print(
                "[Guild cleanup] "
                "ERROR: Unexpected category. "
                "Keeping item."
            )

            continue

        # ----------------------------------
        # Update metadata
        # ----------------------------------

        old_category = item.get(
            "category"
        )

        item["guild_category"] = (
            guild_category
        )

        item["category"] = (
            new_category
        )

        if title_from_guild:

            item["title"] = (
                title_from_guild
            )

        if tags:

            item["tags"] = tags

        asset_type = {
            "グラフィック素材": "graphic",
            "サウンド素材": "sound",
            "プラグイン": "plugin",
        }.get(
            new_category
        )

        if asset_type:

            item["asset_type"] = (
                asset_type
            )

        # ----------------------------------
        # Result
        # ----------------------------------

        if old_category != new_category:

            reclassified += 1

            print(
                "[Guild cleanup] "
                "Reclassify: "
                f"{old_category} -> "
                f"{new_category}"
            )

        else:

            unchanged += 1

        updated_guild.append(
            item
        )

    # ======================================
    # Rebuild pending
    # ======================================

    updated = (
        non_guild_items
        + updated_guild
    )

    with pending_path.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            updated,
            f,
            ensure_ascii=False,
            indent=2,
        )

        f.write(
            "\n"
        )

    # ======================================
    # Summary
    # ======================================

    print()

    print(
        "===== Guild Pending Rebuild Result ====="
    )

    print(
        "Guild items from backup: "
        f"{len(guild_items)}"
    )

    print(
        "Reclassified: "
        f"{reclassified}"
    )

    print(
        "Unchanged target items: "
        f"{unchanged}"
    )

    print(
        "Removed confirmed non-target: "
        f"{removed}"
    )

    print(
        "URL not found / kept: "
        f"{unmatched}"
    )

    print(
        "Errors kept: "
        f"{errors}"
    )

    print(
        "Pending total before: "
        f"{len(current_items)}"
    )

    print(
        "Pending total after: "
        f"{len(updated)}"
    )

    print(
        "Safety backup: "
        f"{safety_backup}"
    )


if __name__ == "__main__":
    main()
