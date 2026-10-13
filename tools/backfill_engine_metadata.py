#!/usr/bin/env python3
"""Create a reviewable preview of historical RPG Maker engine metadata backfill.

Default mode writes transformed copies and a JSON report under
engine_backfill_preview/. It never edits data/archive. Use --apply only when
intentionally ready to modify the source archive files.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

from asset_metadata import detect_engine

ARCHIVE_DIR = Path("data/archive")
PREVIEW_DIR = Path("engine_backfill_preview")
REPORT_NAME = "engine_backfill_preview_report.json"
SPECIFIC_ENGINES = {
    "MZ", "MV", "MV Trinity", "VX Ace", "VX", "XP",
    "2003", "2000", "95", "U2U", "UNITE",
}
PLACEHOLDER_ENGINES = {"不明", "その他RPG Maker"}


def _as_engine_list(value):
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item]
    return []


def propose_engine_update(item):
    """Return a new engine list, or None when no safe metadata change applies."""
    old = _as_engine_list(item.get("engine"))
    detected = detect_engine(item)
    concrete = [name for name in detected if name in SPECIFIC_ENGINES]
    if not concrete:
        return None

    old_concrete = [name for name in old if name in SPECIFIC_ENGINES]
    additions = [name for name in concrete if name not in old_concrete]
    if not additions:
        return None

    # Preserve known concrete engines and their order. Replace generic/unknown
    # placeholders only when concrete evidence exists; retain unrelated values.
    result = [name for name in old if name not in PLACEHOLDER_ENGINES]
    for name in concrete:
        if name not in result:
            result.append(name)
    return result


def transform_archive_data(data, source_file=""):
    """Return transformed copy and a record-level change report."""
    if isinstance(data, list):
        records = data
        container_key = None
    elif isinstance(data, dict) and isinstance(data.get("items"), list):
        records = data["items"]
        container_key = "items"
    else:
        raise ValueError(f"{source_file or 'archive'}: expected a list or an object with an items list")

    # JSON round-trip guarantees the original object is not mutated by this helper.
    cloned = json.loads(json.dumps(data, ensure_ascii=False))
    cloned_records = cloned if container_key is None else cloned[container_key]
    changes = []

    for index, item in enumerate(cloned_records):
        if not isinstance(item, dict):
            continue
        proposed = propose_engine_update(item)
        if proposed is None:
            continue
        old = _as_engine_list(item.get("engine"))
        item["engine"] = proposed
        changes.append({
            "source_file": source_file,
            "record_index": index,
            "internal_id": item.get("internal_id"),
            "title": item.get("title"),
            "url": item.get("url"),
            "old_engine": old,
            "new_engine": proposed,
        })
    return cloned, changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Modify archive files in place (default is preview-only).",
    )
    parser.add_argument(
        "--output-dir",
        default=str(PREVIEW_DIR),
        help="Directory for preview copies and report (default: engine_backfill_preview).",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if not args.apply:
        output_dir.mkdir(parents=True, exist_ok=True)

    all_changes = []
    files_read = 0
    files_skipped = []
    per_file = {}

    for path in sorted(ARCHIVE_DIR.glob("????-??.json")):
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            transformed, changes = transform_archive_data(data, str(path))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            files_skipped.append({"file": str(path), "reason": str(exc)})
            continue

        files_read += 1
        all_changes.extend(changes)
        per_file[str(path)] = {
            "records_changed": len(changes),
            "engine_additions": dict(Counter(
                engine
                for change in changes
                for engine in change["new_engine"]
                if engine not in change["old_engine"]
            )),
        }

        if args.apply:
            path.write_text(json.dumps(transformed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:
            (output_dir / path.name).write_text(
                json.dumps(transformed, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    report = {
        "mode": "apply" if args.apply else "preview_only",
        "files_read": files_read,
        "files_skipped": files_skipped,
        "records_changed": len(all_changes),
        "per_file": per_file,
        "changes": all_changes,
        "note": (
            "Archive files were modified in place."
            if args.apply
            else "Preview copies only; source archive files were not modified."
        ),
    }
    report_path = (output_dir / REPORT_NAME) if not args.apply else Path(REPORT_NAME)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[Engine backfill] Mode: {report['mode']}")
    print(f"[Engine backfill] Files read: {files_read}")
    print(f"[Engine backfill] Files skipped: {len(files_skipped)}")
    print(f"[Engine backfill] Records changed: {len(all_changes)}")
    print(f"[Engine backfill] Report: {report_path}")


if __name__ == "__main__":
    main()
