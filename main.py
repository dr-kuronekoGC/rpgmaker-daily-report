import json
from pathlib import Path

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

from sources.registry import SOURCES
from sources.base import reset_request_stats, get_request_stats
from sources.health import determine_source_status

from item_model import normalize_items
from asset_metadata import enrich_items
from language import detect_language
from archive import save_archive
from tools.apply_review_decisions import apply_decisions

from review_queue import (
    load_review_queue,
    save_review_queue,
    prepare_classification_reviews,
    get_carryover_review_items,
)

from config import (
    PENDING_ITEMS_FILE,
    MAX_ITEMS_PER_SOURCE,
)


GLOBAL_SEEN_FILE = "seen_global.json"
REVIEW_DECISIONS_FILE = Path("data/review/review_decisions.json")


def get_global_key(item):
    """
    複数サイトをまたいだ重複判定用キー。
    """

    # Source Checkは同じURLを繰り返し使うため、
    # global seenでは重複扱いにしない。
    if item.get("category") == "SourceCheck":
        return None

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

    seen_set = set(global_seen)

    for item in items:
        key = get_global_key(item)

        if key is None:
            filtered_items.append(item)
            continue

        if key in seen_set:
            continue

        filtered_items.append(item)
        new_global_seen.append(key)
        seen_set.add(key)

    return (
        filtered_items,
        new_global_seen,
    )


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
    サイトごとに最大件数を選択する。

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


def assign_language_if_missing(item):
    """
    サイト側が明示した言語情報を優先する。
    Source Checkのタイトルは日本語で生成されるため、
    タイトルから再判定するとサイト言語を誤って上書きする。
    """
    if not isinstance(item, dict):
        return None

    if item.get("language"):
        return item["language"]

    language = detect_language(
        title=item.get("title", ""),
        description=item.get("description", ""),
        tags=item.get("tags", []),
    )

    if language is not None:
        item["language"] = language

    return item.get("language")


def main():
    pending_seen = []
    all_items = []
    source_results = []

    global_seen = load_seen_file(
        GLOBAL_SEEN_FILE
    )

    pending_items = load_pending_items(
        PENDING_ITEMS_FILE
    )

    review_queue = load_review_queue()

    # Human decisions are committed as an explicit input file. Import them
    # before collection so resolved PRE items stop appearing in carryover.
    if REVIEW_DECISIONS_FILE.exists():
        with REVIEW_DECISIONS_FILE.open("r", encoding="utf-8") as handle:
            decision_payload = json.load(handle)
        updated_review_queue, decision_summary = apply_decisions(
            review_queue,
            decision_payload,
        )
        if decision_summary["applied"]:
            save_review_queue(updated_review_queue)
            review_queue = updated_review_queue
        print(
            "[Classification review decisions] "
            f"Requested: {decision_summary['requested']} / "
            f"Applied: {decision_summary['applied']} / "
            f"Already applied: {decision_summary['already_applied']}"
        )

    for source in SOURCES:
        collector_name = source.__name__.split(".")[-1]
        seen_before = None

        reset_request_stats()
        try:
            seen = load_seen_file(
                source.SEEN_FILE
            )
            seen_before = len(seen)

            items, new_seen = source.get_items(
                seen
            )

            items = normalize_items(
                items,
                collector_name,
            )

            all_items.extend(items)

            pending_seen.append(
                (
                    source,
                    new_seen,
                )
            )

            # A collector may catch an individual page error and return normally.
            # Combine its own summary with shared HTTP diagnostics so that a
            # caught 403/429/timeout is not automatically reported as healthy.
            summary = getattr(source, "LAST_RUN_SUMMARY", None)
            request_stats = get_request_stats()
            status = determine_source_status(request_stats, summary)
            source_results.append({
                "name": collector_name,
                "status": status,
                "new_items": len(items),
                "seen_before": seen_before,
                "seen_after": len(new_seen),
                "summary": summary,
                "request_stats": request_stats,
            })

        except Exception as e:
            print(
                f"[{source.__name__}] Error: {e}"
            )
            source_results.append({
                "name": collector_name,
                "status": "ERROR",
                "error_type": type(e).__name__,
                "seen_before": seen_before,
                "request_stats": get_request_stats(),
            })

    successful_sources = sum(
        result["status"] == "OK"
        for result in source_results
    )
    partial_sources = sum(
        result["status"] == "PARTIAL"
        for result in source_results
    )
    failed_sources = sum(
        result["status"] == "ERROR"
        for result in source_results
    )

    print(
        "[Source Health] "
        f"OK: {successful_sources}/{len(source_results)} / "
        f"PARTIAL: {partial_sources} / "
        f"ERROR: {failed_sources}"
    )
    for result in source_results:
        status = result["status"]
        if status in ("OK", "PARTIAL"):
            print(
                "[Source Health] "
                f"{result['name']}: {status} / "
                f"new={result['new_items']} / "
                f"seen={result['seen_before']}->{result['seen_after']}"
            )
            summary = result.get("summary")
            request_stats = result.get("request_stats", {})
            if request_stats.get("failed", 0) or status == "PARTIAL":
                print(
                    "[Source Health] "
                    f"{result['name']} requests: "
                    f"success={request_stats.get('succeeded', 0)} / "
                    f"failed={request_stats.get('failed', 0)}"
                )
            if status == "PARTIAL" and isinstance(summary, dict):
                print(
                    "[Source Health] "
                    f"{result['name']} details: "
                    f"checked={summary.get('checked', 0)} / "
                    f"updated={summary.get('updated', 0)} / "
                    f"baseline={summary.get('baseline', 0)} / "
                    f"unchanged={summary.get('unchanged', 0)} / "
                    f"failed={summary.get('failed', 0)}"
                )
        else:
            request_stats = result.get("request_stats", {})
            print(
                "[Source Health] "
                f"{result['name']}: ERROR / "
                f"type={result.get('error_type', 'caught_request_failure')} / "
                f"requests={request_stats.get('succeeded', 0)} succeeded,"
                f"{request_stats.get('failed', 0)} failed / "
                f"seen_before={result['seen_before']}"
            )

    # パーサー更新による既存Archiveの修正項目は、
    # 新着・分類確認・Pendingには流さず、Archiveだけ更新する。
    archive_update_items = [
        item
        for item in all_items
        if item.get("_update_existing")
    ]

    all_items = [
        item
        for item in all_items
        if not item.get("_update_existing")
    ]

    if archive_update_items:
        print(
            "[Archive Update] Items:",
            len(archive_update_items),
        )

        # パーサー更新で再取得した既存Itemも、通常の新着Itemと同じ
        # 共通メタデータ処理を通してからArchiveへ戻す。
        archive_update_items = enrich_items(
            archive_update_items
        )

    for item in all_items:
        assign_language_if_missing(item)

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
        len(all_items),
    )


    # 共通分類・メタデータ付与は、global seenの後に一度だけ実行する。
    all_items = enrich_items(all_items)

    # 言語は互換用の language と、DB用の languages[] の両方に保持する。
    for item in all_items:
        language = item.get("language")
        languages = item.get("languages", [])
        if language and language not in languages:
            item["languages"] = [*languages, language]

    # 初期データ取り込み中のItemはArchiveには保存するが、
    # Slackの通常レポート・分類確認には出さない。
    reportable_items = [
        item
        for item in all_items
        if not item.get("_suppress_report")
    ]

    review_items = prepare_classification_reviews(
        reportable_items,
        review_queue,
    )

    carryover_review_items = get_carryover_review_items(
        review_queue,
        review_items,
    )

    print(
        "[Classification review] New:",
        len(review_items),
    )

    print(
        "[Classification review] Carryover:",
        len(carryover_review_items),
    )

    # 分類確認キューはSlack送信失敗時にも失わないよう、
    # Archive保存と同じくこの時点で永続化する。
    save_review_queue(
        review_queue
    )

    save_archive(
        archive_update_items + all_items
    )

    pending_items = add_to_pending(
        pending_items,
        reportable_items,
    )

    print(
        "[Pending] Before selection:",
        len(pending_items),
    )

    report_items, remaining_pending = (
        select_pending_items(
            pending_items
        )
    )

    print(
        "[Pending] Selected:",
        len(report_items),
    )

    print(
        "[Pending] Remaining:",
        len(remaining_pending),
    )

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
        ],
    )

    report = build_report(
        report_items,
        review_items,
        carryover_review_items,
        source_results=source_results,
    )

    print()
    print("----- REPORT -----")
    print(report)

    slack_success = send_to_slack(
        report
    )

    if slack_success:
        for source, new_seen in pending_seen:
            save_seen_file(
                source.SEEN_FILE,
                new_seen,
            )

        save_seen_file(
            GLOBAL_SEEN_FILE,
            new_global_seen,
        )

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
