# ==========================================
# Rebuild old RPG Maker Guild pending items
# ==========================================

import json
import re
import shutil
import sys
import time
from pathlib import Path

import requests


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
# Rate Limit
# ==========================================

REQUEST_INTERVAL = 1.5

MAX_RETRIES = 4

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
    """
    素材カテゴリを
    グラフィック / サウンドに分類する。
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


def classify_topic(
    category,
    title,
    tags,
):
    """
    Guildカテゴリを
    Daily Reportカテゴリへ変換する。

    重要：
    categoryが空の場合はNoneを返す。
    これは「削除」ではなく、
    「判定不能」として扱う。
    """

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
# Topic API
# ==========================================

def topic_api_url(url):

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

    戻り値：
        category
        title
        tags

    取得できなかった場合は例外を発生させる。

    「カテゴリが空」はエラーではないが、
    判定不能として扱う。
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

            # ------------------------------
            # 429
            # ------------------------------

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

            data = response.json()

            # ----------------------------------
            # Category
            # ----------------------------------

            category = (
                data.get(
                    "category_name"
                )
                or ""
            ).strip()

            # ----------------------------------
            # Title
            # ----------------------------------

            title = (
                data.get(
                    "title"
                )
                or ""
            ).strip()

            # ----------------------------------
            # Tags
            # ----------------------------------

            tags = data.get(
                "tags"
            ) or []

            if not isinstance(
                tags,
                list,
            ):
                tags = []

            tags = [
                tag.strip()
                for tag in tags
                if isinstance(
                    tag,
                    str,
                )
                and tag.strip()
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
                f"Waiting "
                f"{wait_seconds}s "
                "before retry."
            )

            time.sleep(
                wait_seconds
            )

    raise RuntimeError(
        "Unable to fetch Guild topic"
    )


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
    # Process
    # ======================================

    session = requests.Session()

    updated_guild = []

    reclassified = 0
    unchanged = 0
    removed = 0
    errors = 0
    unknown = 0

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

        # ----------------------------------
        # URL missing
        # ----------------------------------

        if not isinstance(
            url,
            str,
        ) or not url.strip():

            # 絶対に削除しない。
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

        try:

            (
                category,
                topic_title,
                tags,
            ) = fetch_topic(
                session,
                url,
            )

            # ==================================
            # 最重要安全チェック
            # ==================================

            if not category:

                # ----------------------------------
                # カテゴリ不明
                # ----------------------------------
                #
                # ここでは絶対に削除しない。
                #
                # 前回の事故はここで起きた。
                # ----------------------------------

                unknown += 1

                updated_guild.append(
                    item
                )

                print(
                    "[Guild cleanup] "
                    "UNKNOWN CATEGORY. "
                    "Keeping item: "
                    f"{title}"
                )

                time.sleep(
                    REQUEST_INTERVAL
                )

                continue

            # ----------------------------------
            # Daily Report category
            # ----------------------------------

            new_category = classify_topic(
                category,
                topic_title or title,
                tags,
            )

            # ==================================
            # 明確に対象外
            # ==================================

            if new_category is None:

                removed += 1

                print(
                    "[Guild cleanup] "
                    "Remove confirmed "
                    "non-target: "
                    f"{category} | "
                    f"{title}"
                )

                time.sleep(
                    REQUEST_INTERVAL
                )

                continue

            # ----------------------------------
            # Metadata update
            # ----------------------------------

            old_category = item.get(
                "category"
            )

            item["guild_category"] = (
                category
            )

            item["category"] = (
                new_category
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

            time.sleep(
                REQUEST_INTERVAL
            )

        except Exception as e:

            # ==================================
            # エラー時も絶対に削除しない
            # ==================================

            errors += 1

            updated_guild.append(
                item
            )

            print(
                "[Guild cleanup] "
                f"ERROR: {url} | {e}"
            )

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
        "Unknown category kept: "
        f"{unknown}"
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
