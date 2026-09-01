from common import (
    load_seen_file,
    save_seen_file,
    load_pending_items,
    save_pending_items,
)

from report import (
    build_report,
    send_to_slack,
)

from sources import (
    community_reddit,
    community_forum,
    official_site,
    official_steam,
    official_opengameart,
    official_kenney,
    official_craftpix,
    official_gamedevmarket,
    official_visustella,
    official_deviantart,
    asset_itchio,
    official_makerdevs,
)

from asset_metadata import enrich_items
from language import detect_language
from archive import save_archive

from config import (
    PENDING_ITEMS_FILE,
    MAX_ITEMS_PER_SOURCE,
)


SOURCES = [
    community_reddit,
    official_site,
    official_steam,
    official_opengameart,
    official_kenney,
    official_craftpix,
    official_gamedevmarket,
    official_visustella,
    official_deviantart,
    asset_itchio,
    community_forum,
    official_makerdevs,
]


# ==========================================
# Global seen
# ==========================================

GLOBAL_SEEN_FILE = "seen_global.json"


def get_global_key(item):
    """
    複数サイトをまたいだ重複判定用キー。
    """

    url = item.get("url")

    if isinstance(url, str):
        url = url.strip()

        if url:
            return f"url:{url}"

    return None


def filter_global_seen(
    items,
    global_seen,
):

    filtered_items = []
    new_global_seen = list(global_seen)

    seen_set = set(
        global_seen
    )

    for item in items:

        # ==================================
        # Forum BackfillはGlobal seen対象外
        # ==================================

        if item.get(
            "forum_backfill",
            False,
        ):

            filtered_items.append(
                item
            )

            continue

        key = get_global_key(
            item
        )

        if key is None:

            filtered_items.append(
                item
            )

            continue

        if key in seen_set:

            continue

        filtered_items.append(
            item
        )

        new_global_seen.append(
            key
        )

        seen_set.add(
            key
        )

    return (
        filtered_items,
        new_global_seen,
    )


# ==========================================
# Pending
# ==========================================

def get_pending_key(item):
    """
    掲載待ちItemの重複判定用キー。

    URLを基本キーとする。
    """

    url = item.get("url")

    if isinstance(url, str):
        url = url.strip()

        if url:
            return url

    return None


def add_to_pending(
    pending_items,
    new_items,
):
    """
    新規Itemを掲載待ちに追加する。

    同じURLは重複して追加しない。
    """

    existing_keys = {
        get_pending_key(item)
        for item in pending_items
        if get_pending_key(item) is not None
    }

    for item in new_items:

        key = get_pending_key(item)

        if key is not None:

            if key in existing_keys:
                continue

            existing_keys.add(key)

        pending_items.append(item)

    return pending_items


def select_pending_items(
    pending_items,
):
    """
    サイトごとに最大20件を選択する。

    pending_itemsの先頭から順番に処理するため、
    古い掲載待ちから先に掲載される。
    """

    selected = []
    counts = {}

    remaining = []

    for item in pending_items:

        source = item.get(
            "source",
            "Unknown",
        )

        count = counts.get(
            source,
            0,
        )

        if count < MAX_ITEMS_PER_SOURCE:

            selected.append(item)

            counts[source] = count + 1

        else:

            remaining.append(item)

    return (
        selected,
        remaining,
    )


def main():

    pending_seen = []
    all_items = []

    # ======================================
    # Global seen
    # ======================================

    global_seen = load_seen_file(
        GLOBAL_SEEN_FILE
    )

    # ======================================
    # Pending
    # ======================================

    pending_items = load_pending_items(
        PENDING_ITEMS_FILE
    )

    # ======================================
    # Source collection
    # ======================================

    for source in SOURCES:

        try:

            seen = load_seen_file(
                source.SEEN_FILE
            )

            items, new_seen = source.get_items(
                seen
            )

            all_items.extend(
                items
            )

            pending_seen.append(
                (
                    source,
                    new_seen,
                )
            )

        except Exception as e:

            print(
                f"[{source.__name__}] Error: {e}"
            )

    # ======================================
    # Language detection
    # ======================================

    for item in all_items:

        language = detect_language(
            title=item.get("title", ""),
            description=item.get(
                "description",
                "",
            ),
            tags=item.get(
                "tags",
                [],
            ),
        )

        if language is not None:

            item["language"] = language

    # ======================================
    # Cross-source duplicate filtering
    # ======================================

    all_items, new_global_seen = filter_global_seen(
        all_items,
        global_seen,
    )

    print(
        "[Global seen] "
        f"Before: {len(global_seen)} / "
        f"After: {len(new_global_seen)} / "
        f"New: {len(new_global_seen) - len(global_seen)}"
    )

    print(
        "[DEBUG] Items after global seen:",
        len(all_items)
    )

    # ======================================
    # Asset metadata
    # ======================================

    all_items = enrich_items(
        all_items
    )

    print(
        "[DEBUG] Items after enrich:",
        len(all_items)
    )

    # ======================================
    # Archive
    # ======================================

    save_archive(
        all_items
    )

    # ======================================
    # Add new items to pending
    # ======================================

    pending_items = add_to_pending(
        pending_items,
        all_items,
    )

    print(
        "[Pending] Before selection:",
        len(pending_items)
    )

    # ======================================
    # Select items for this report
    # ======================================

    report_items, remaining_pending = (
        select_pending_items(
            pending_items
        )
    )

    print(
        "[Pending] Selected:",
        len(report_items)
    )

    print(
        "[Pending] Remaining:",
        len(remaining_pending)
    )

    # ======================================
    # Debug
    # ======================================

    for item in report_items:

        print(
            "[DEBUG] Item:",
            item.get("source"),
            "|",
            item.get("category"),
            "|",
            item.get("title"),
        )

    print(
        "[DEBUG] Categories:",
        [
            item.get("category")
            for item in report_items
        ]
    )

    # ======================================
    # Report
    # ======================================

    report = build_report(
        report_items
    )

    print()
    print("----- REPORT -----")
    print(report)

    slack_success = send_to_slack(
        report
    )

    if slack_success:

        # ======================================
        # Save seen
        # ======================================

        for source, new_seen in pending_seen:

            save_seen_file(
                source.SEEN_FILE,
                new_seen,
            )

        save_seen_file(
            GLOBAL_SEEN_FILE,
            new_global_seen,
        )

        # ======================================
        # Forum Archive Progress
        # ======================================

        if hasattr(
            community_forum,
            "finalize",
        ):

            community_forum.finalize()

        # ======================================
        # Save pending
        # ======================================
        #
        # Slack送信成功時のみ、
        # 今回掲載したItemをpendingから削除する。
        #

        save_pending_items(
            PENDING_ITEMS_FILE,
            remaining_pending,
        )

        print(
            "[Pending] Saved after successful Slack delivery."
        )

    else:

        print(
            "[Pending] Slack送信失敗のため、"
            "seen/pendingを更新しません。"
        )

if __name__ == "__main__":
    main()
