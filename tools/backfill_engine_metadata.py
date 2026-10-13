#!/usr/bin/env python3
"""Create a preview of historical RPG Maker engine metadata changes.

This tool is deliberately read-only with respect to data/archive. It writes
transformed copies and a change/conflict report under engine_backfill_preview/.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
from asset_metadata import detect_engine

ARCHIVE_DIR = Path("data/archive")
PREVIEW_DIR = Path("engine_backfill_preview")
REPORT_NAME = "engine_backfill_preview_report.json"
SPECIFIC_ENGINES = {"MZ", "MV", "MV Trinity", "VX Ace", "VX", "XP", "2003", "2000", "95", "U2U", "UNITE"}
PLACEHOLDER_ENGINES = {"不明", "その他RPG Maker"}


def _as_engine_list(value):
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item]
    return []


def _specific_engines(item):
    metadata_only = {key: value for key, value in item.items() if key != "engine"}
    return [name for name in detect_engine(metadata_only) if name in SPECIFIC_ENGINES]


def propose_engine_update(item):
    """Return a new engine list, or None when no safe metadata change applies."""
    old = _as_engine_list(item.get("engine"))
    concrete = _specific_engines(item)
    if not concrete:
        return None
    old_concrete = [name for name in old if name in SPECIFIC_ENGINES]
    # Existing specific engine metadata is intentionally left untouched.
    # Detector matches may come from broad tags or compatibility references,
    # so only placeholder-only records are eligible for this bulk backfill.
    if old_concrete:
        return None
    result = [name for name in old if name not in PLACEHOLDER_ENGINES]
    for name in concrete:
        if name not in result:
            result.append(name)
    return result


def transform_archive_data(data, source_file=""):
    """Return transformed copy, safe changes, and conflicting records."""
    if isinstance(data, list):
        container_key = None
    elif isinstance(data, dict) and isinstance(data.get("items"), list):
        container_key = "items"
    else:
        raise ValueError(f"{source_file or 'archive'}: expected a list or an object with an items list")
    cloned = json.loads(json.dumps(data, ensure_ascii=False))
    cloned_records = cloned if container_key is None else cloned[container_key]
    changes, conflicts = [], []
    for index, item in enumerate(cloned_records):
        if not isinstance(item, dict):
            continue
        old = _as_engine_list(item.get("engine"))
        concrete = _specific_engines(item)
        old_concrete = [name for name in old if name in SPECIFIC_ENGINES]
        if old_concrete and concrete and not set(old_concrete).intersection(concrete):
            conflicts.append({
                "source_file": source_file, "record_index": index,
                "internal_id": item.get("internal_id"), "title": item.get("title"),
                "url": item.get("url"), "old_engine": old, "detected_engine": concrete,
            })
            continue
        proposed = propose_engine_update(item)
        if proposed is None:
            continue
        item["engine"] = proposed
        changes.append({
            "source_file": source_file, "record_index": index,
            "internal_id": item.get("internal_id"), "title": item.get("title"),
            "url": item.get("url"), "old_engine": old, "new_engine": proposed,
        })
    return cloned, changes, conflicts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(PREVIEW_DIR), help="Directory for preview copies and report.")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_changes, all_conflicts = [], []
    files_read, files_skipped, per_file = 0, [], {}
    for path in sorted(ARCHIVE_DIR.glob("????-??.json")):
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            transformed, changes, conflicts = transform_archive_data(data, str(path))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            files_skipped.append({"file": str(path), "reason": str(exc)})
            continue
        files_read += 1
        all_changes.extend(changes)
        all_conflicts.extend(conflicts)
        per_file[str(path)] = {
            "records_changed": len(changes), "conflicts": len(conflicts),
            "engine_additions": dict(Counter(
                engine for change in changes for engine in change["new_engine"]
                if engine not in change["old_engine"]
            )),
        }
        (output_dir / path.name).write_text(
            json.dumps(transformed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    report = {
        "mode": "preview_only", "files_read": files_read, "files_skipped": files_skipped,
        "records_changed": len(all_changes), "conflict_count": len(all_conflicts),
        "per_file": per_file, "changes": all_changes, "conflicts": all_conflicts,
        "note": "Preview copies only; source archive files were not modified.",
    }
    report_path = output_dir / REPORT_NAME
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[Engine backfill] Files read: {files_read}")
    print(f"[Engine backfill] Files skipped: {len(files_skipped)}")
    print(f"[Engine backfill] Records changed: {len(all_changes)}")
    print(f"[Engine backfill] Conflicting records held for review: {len(all_conflicts)}")
    print(f"[Engine backfill] Report: {report_path}")


if __name__ == "__main__":
    main()
