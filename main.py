from common import (
    load_seen_file,
    save_seen_file,
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
)

from asset_metadata import enrich_items


SOURCES = [
    community_reddit,
    official_site,
    official_steam,
    official_opengameart,
    official_kenney,
    official_craftpix,
    official_visustella,
    official_deviantart,
    asset_itchio,
    community_forum,
]


# ==========================================
# Global seen
# ==========================================

GLOBAL_SEEN_FILE = "seen_global.json"


def get_global_key(item):
    """
    複数サイトをまたいだ重複判定用キー。

    現段階ではURLを基本キーとする。
    URLが同じ記事・素材であれば、別サイトから取得されても
    2回目以降はレポートに表示しない。

    タイトルだけで判定すると、別物なのに同名の記事を
    誤って除外する可能性があるため、現段階では採用しない。
    """

    url = item.get("url")

    if isinstance(url, str):
        url = url.strip()

        if url:
            return f"url:{url}"

    return None


def filter_global_seen(items, global_seen):
    """
    複数サイトをまたいだ既読情報を除外する。

    戻り値:
        filtered_items:
            今回レポートに採用する項目

        new_global_seen:
            今回新たに既読登録するキー
    """

    filtered_items = []
    new_global_seen = list(global_seen)

    seen_set = set(global_seen)

    for item in items:

        key = get_global_key(item)

        # URLが取得できない項目は、
        # 現段階ではグローバル既読判定の対象にしない。
        if key is None:
            filtered_items.append(item)
            continue

        # 過去に別サイトを含めて取得済みなら除外
        if key in seen_set:
            continue

        filtered_items.append(item)

        new_global_seen.append(key)
        seen_set.add(key)

    return (
        filtered_items,
        new_global_seen,
    )


def main():
    pending_seen = []
    all_items = []

    # サイトごとの既読管理とは別に、
    # 全サイト共通の既読情報を読み込む。
    global_seen = load_seen_file(
        GLOBAL_SEEN_FILE
    )

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

    for item in all_items:
        print(
            "[DEBUG] Item:",
            item.get("source"),
            "|",
            item.get("category"),
            "|",
            item.get("title"),
        )

    # ======================================
    # Report
    # ======================================

    report = build_report(
        all_items
    )

    print()
    print("----- REPORT -----")
    print(report)

    send_to_slack(
    report
    )

    # ======================================
    # Seen 保存
    # ======================================
    #
    # Slackへのレポート作成・送信まで成功した後に
    # 初めて既読として保存する。
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

if __name__ == "__main__":
    main()
