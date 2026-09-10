# ==========================================
# Reclassify old RPG Maker Guild pending items
# ==========================================

import json
import re
import shutil
import sys
import time
from pathlib import Path

import requests


ROOT_DIR = Path(
    __file__
).resolve().parent.parent

sys.path.insert(
    0,
    str(ROOT_DIR),
)

from config import (
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

TARGET_CATEGORIES = {
    "素材",
    "プラグイン",
    "RPG Makerプラグイン",
    "RGSSx",
}


# ==========================================
# Rate Limit Settings
# ==========================================

# 通常のリクエスト間隔。
REQUEST_INTERVAL = 1.2

# 429発生時の最大リトライ回数。
MAX_RETRIES = 4

# Retry-Afterが取得できない場合の待機時間。
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


# ==========================================
# Classification
# ==========================================

def classify_material(
    title,
    tags,
):

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


def classify_topic(
    category,
    title,
    tags,
):

    if category in {
        "プラグイン",
        "RPG Makerプラグイン",
        "RGSSx",
    }:

        return "プラグイン"

    if category == "素材":

        return classify_material(
            title,
            tags,
        )

    return None


# ==========================================
# Guild Topic API
# ==========================================

def topic_api_url(url):
    """
    Discourse topic URLをJSON API URLへ変換する。
    """

    url = url.rstrip("/")

    if url.endswith(".json"):
        return url

    return f"{url}.json"


def fetch_topic(
    session,
    url,
):
    """
    Guild Topic APIを取得する。

    429の場合はRetry-Afterを尊重して
    最大MAX_RETRIES回まで再試行する。
    """

    api_url = topic_api_url(
        url
    )

    for attempt in range(
        MAX_RETRIES + 1
    ):

        try:

            response = session.get(
                api_url,
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

                # 念のため上限を設定。
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
                    f"Waiting {wait_seconds:.1f}s "
                    f"(retry {attempt + 1}/"
                    f"{MAX_RETRIES})"
                )

                time.sleep(
                    wait_seconds
                )

                continue

            response.raise_for_status()

            data = response.json()

            category = (
                data.get(
                    "category_name"
                )
                or ""
            )

            title = (
                data.get(
                    "title"
                )
                or ""
            )

            tags = (
                data.get(
                    "tags"
                )
                or []
            )

            if not isinstance(
                tags,
                list,
            ):

                tags = []

            tags = [
                tag
                for tag in tags
                if isinstance(
                    tag,
                    str,
                )
            ]

            return (
                category,
                title,
                tags,
            )

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
                f"Waiting {wait_seconds}s "
                f"before retry."
            )

            time.sleep(
                wait_seconds
            )

    raise RuntimeError(
        "Unable to fetch Guild topic"
    )


# ==========================================
# Backup Handling
# ==========================================

def get_backup_path(
    pending_path,
):

    return pending_path.with_name(
        pending_path.name
        + ".guild_cleanup_backup"
    )


def load_json(
    path,
):

    with path.open(
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)


# ==========================================
# Main
# ==========================================

def main():

    pending_path = Path(
        PENDING_ITEMS_FILE
    )

    if not pending_path.exists():

        raise FileNotFoundError(
            f"Pending file not found: "
            f"{pending_path}"
        )

    backup_path = get_backup_path(
        pending_path
    )

    if not backup_path.exists():

        raise FileNotFoundError(
            "Guild cleanup backup not found: "
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
            "pending_items.json is not a list"
        )

    # --------------------------------------
    # Backup
    # --------------------------------------

    backup_items = load_json(
        backup_path
    )

    if not isinstance(
        backup_items,
        list,
    ):

        raise ValueError(
            "Guild cleanup backup is not a list"
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
    # Restore ALL Guild items from the
    # original cleanup backup.
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
        "Guild items from original backup: "
        f"{len(guild_items)}"
    )

    print(
        "Non-Guild items preserved: "
        f"{len(non_guild_items)}"
    )

    session = requests.Session()

    updated_guild = []

    reclassified = 0
    unchanged = 0
    removed = 0
    errors = 0

    # ======================================
    # Process Guild items
    # ======================================

    for index, item in enumerate(
        guild_items,
        start=1,
    ):

        url = item.get(
            "url"
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

        if not isinstance(
            url,
            str,
        ) or not url.strip():

            print(
                "[Guild cleanup] "
                "Missing URL; removing."
            )

            removed += 1

            continue

        try:

            (
                category,
                topic_title,
                tags,
            ) = fetch_topic(
                session,
                url,
            )

            new_category = classify_topic(
                category,
                topic_title
                or title,
                tags,
            )

            # ----------------------------------
            # Non-target category
            # ----------------------------------

            if new_category is None:

                print(
                    "[Guild cleanup] "
                    "Remove non-target: "
                    f"{category} | "
                    f"{title}"
                )

                removed += 1

                # 次のAPIアクセスまで少し待つ。
                time.sleep(
                    REQUEST_INTERVAL
                )

                continue

            old_category = item.get(
                "category"
            )

            # ----------------------------------
            # Update metadata
            # ----------------------------------

            item["guild_category"] = (
                category
            )

            if tags:

                item["tags"] = tags

            item["category"] = (
                new_category
            )

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

            # ----------------------------------
            # Rate limit prevention
            # ----------------------------------

            time.sleep(
                REQUEST_INTERVAL
            )

        except Exception as e:

            # API取得失敗の場合は削除しない。
            errors += 1

            updated_guild.append(
                item
            )

            print(
                "[Guild cleanup] ERROR: "
                f"{url} | {e}"
            )

            # エラー時も少し間隔を置く。
            time.sleep(
                REQUEST_INTERVAL
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

        f.write("\n")

    # ======================================
    # Summary
    # ======================================

    print()
    print(
        "===== Guild Pending Rebuild Result ====="
    )

    print(
        f"Guild items from backup: "
        f"{len(guild_items)}"
    )

    print(
        f"Reclassified: "
        f"{reclassified}"
    )

    print(
        f"Unchanged target items: "
        f"{unchanged}"
    )

    print(
        f"Removed non-target items: "
        f"{removed}"
    )

    print(
        f"Errors kept in pending: "
        f"{errors}"
    )

    print(
        f"Pending total before: "
        f"{len(current_items)}"
    )

    print(
        f"Pending total after: "
        f"{len(updated)}"
    )

    print(
        f"Safety backup: "
        f"{safety_backup}"
    )


if __name__ == "__main__":
    main()
