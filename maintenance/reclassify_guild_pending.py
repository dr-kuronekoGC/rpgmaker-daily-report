# ==========================================
# Reclassify old RPG Maker Guild pending items
# ==========================================

import json
import re
import shutil
from pathlib import Path

import requests

from config import PENDING_ITEMS_FILE, REQUEST_TIMEOUT


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(compatible; RPGMakerDailyReport/1.0)"
    )
}

GUILD_SOURCE = "RPG Maker Guild"

TARGET_CATEGORIES = {
    "素材",
    "プラグイン",
    "RGSSx",
}

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

def classify_material(title, tags):

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

    if category == "プラグイン":
        return "プラグイン"

    if category == "RGSSx":
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

    例:
        /t/topic/123
        ->
        /t/topic/123.json
    """

    url = url.rstrip("/")

    if url.endswith(".json"):
        return url

    return f"{url}.json"


def fetch_topic(
    session,
    url,
):

    response = session.get(
        topic_api_url(url),
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    category = (
        data.get("category_name")
        or ""
    )

    title = (
        data.get("title")
        or ""
    )

    tags = (
        data.get("tags")
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


# ==========================================
# Main
# ==========================================

def main():

    pending_path = Path(
        PENDING_ITEMS_FILE
    )

    if not pending_path.exists():

        raise FileNotFoundError(
            f"Pending file not found: {pending_path}"
        )

    with pending_path.open(
        "r",
        encoding="utf-8",
    ) as f:

        pending_items = json.load(f)

    if not isinstance(
        pending_items,
        list,
    ):

        raise ValueError(
            "pending_items.json is not a list"
        )

    # --------------------------------------
    # Backup
    # --------------------------------------

    backup_path = pending_path.with_name(
        pending_path.name
        + ".guild_cleanup_backup"
    )

    shutil.copy2(
        pending_path,
        backup_path,
    )

    session = requests.Session()

    updated = []

    guild_total = 0
    reclassified = 0
    removed = 0
    unchanged = 0
    errors = 0

    # ======================================
    # Process
    # ======================================

    for item in pending_items:

        # Guild以外は完全にそのまま残す。
        if item.get(
            "source"
        ) != GUILD_SOURCE:

            updated.append(
                item
            )

            continue

        guild_total += 1

        url = item.get(
            "url"
        )

        if not isinstance(
            url,
            str,
        ) or not url.strip():

            print(
                "[Guild cleanup] "
                "Missing URL; removing item: "
                f"{item.get('title', '')}"
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
                or item.get(
                    "title",
                    "",
                ),
                tags,
            )

            # ----------------------------------
            # 対象外カテゴリ
            # ----------------------------------

            if new_category is None:

                print(
                    "[Guild cleanup] "
                    "Remove non-target category: "
                    f"{category} | "
                    f"{item.get('title', '')}"
                )

                removed += 1

                continue

            old_category = item.get(
                "category"
            )

            # 現在のGuildカテゴリを記録。
            item["guild_category"] = (
                category
            )

            # 既存タグがない場合のみ補完。
            if (
                not item.get("tags")
                and tags
            ):

                item["tags"] = tags

            # 正しいDaily Reportカテゴリへ更新。
            item["category"] = (
                new_category
            )

            # 古いasset_typeも更新。
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
            # 結果
            # ----------------------------------

            if old_category != new_category:

                reclassified += 1

                print(
                    "[Guild cleanup] "
                    "Reclassify: "
                    f"{old_category} -> "
                    f"{new_category} | "
                    f"{item.get('title', '')}"
                )

            else:

                unchanged += 1

            updated.append(
                item
            )

        except Exception as e:

            # 通信失敗などの場合は、
            # データを削除せずそのまま残す。
            errors += 1

            updated.append(
                item
            )

            print(
                "[Guild cleanup] ERROR: "
                f"{url} | {e}"
            )

    # ======================================
    # Save
    # ======================================

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
        "===== Guild Pending Cleanup ====="
    )

    print(
        f"Guild pending items: {guild_total}"
    )

    print(
        f"Reclassified: {reclassified}"
    )

    print(
        f"Unchanged target items: {unchanged}"
    )

    print(
        f"Removed non-target items: {removed}"
    )

    print(
        f"Errors kept in pending: {errors}"
    )

    print(
        f"Pending total before: "
        f"{len(pending_items)}"
    )

    print(
        f"Pending total after: "
        f"{len(updated)}"
    )

    print(
        f"Backup: {backup_path}"
    )


if __name__ == "__main__":
    main()
