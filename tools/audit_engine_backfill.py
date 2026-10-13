#!/usr/bin/env python3
"""Read-only audit of engine metadata candidates and conflicting detections."""
import json
from collections import Counter
from pathlib import Path
from asset_metadata import detect_engine

ARCHIVE_DIR = Path("data/archive")
OUTPUT_FILE = Path("engine_backfill_audit.json")
SPECIFIC_ENGINES = {"MZ", "MV", "MV Trinity", "VX Ace", "VX", "XP", "2003", "2000", "95", "U2U", "UNITE"}


def _as_engine_list(value):
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item]
    return []


def _evidence_fields(item):
    result = []
    for field in ("title", "description", "body_text", "post_body", "source_tags", "tags", "url"):
        value = item.get(field)
        if isinstance(value, str) and value.strip():
            result.append({"field": field, "text": value.strip()[:500]})
        elif isinstance(value, list) and value:
            result.append({"field": field, "text": ", ".join(str(x) for x in value[:20])[:500]})
    return result


def audit_records(records, source_file=""):
    summary = Counter()
    candidates = []
    conflicts = []
    for item in records:
        if not isinstance(item, dict):
            summary["invalid_records"] += 1
            continue
        summary["records"] += 1
        old = _as_engine_list(item.get("engine"))
        if not old or "不明" in old:
            summary["records_with_unknown_engine"] += 1
        if "その他RPG Maker" in old:
            summary["records_with_generic_rpg_maker"] += 1
        detected = detect_engine({key: value for key, value in item.items() if key != "engine"})
        concrete = [engine for engine in detected if engine in SPECIFIC_ENGINES]
        old_concrete = [engine for engine in old if engine in SPECIFIC_ENGINES]
        additions = [engine for engine in concrete if engine not in old_concrete]
        if not additions:
            continue
        record = {
            "source_file": source_file, "internal_id": item.get("internal_id"),
            "title": item.get("title"), "url": item.get("url"),
            "source": item.get("source"), "collector": item.get("collector"),
            "old_engine": old, "proposed_engine": detected,
            "new_specific_engines": additions, "evidence": _evidence_fields(item),
        }
        if old_concrete and not set(old_concrete).intersection(concrete):
            summary["engine_conflict_records"] += 1
            conflicts.append(record)
            continue
        summary["candidate_records"] += 1
        for engine in additions:
            summary["candidate_engine_" + engine.replace(" ", "_")] += 1
        candidates.append(record)
    return dict(summary), candidates, conflicts


def main():
    totals = Counter()
    candidates, conflicts = [], []
    files_read, files_skipped, per_file = 0, [], {}
    for path in sorted(ARCHIVE_DIR.glob("????-??.json")):
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            files_skipped.append({"file": str(path), "reason": str(exc)})
            continue
        if isinstance(data, dict):
            records = data.get("items", [])
        elif isinstance(data, list):
            records = data
        else:
            files_skipped.append({"file": str(path), "reason": "unexpected JSON root type"})
            continue
        if not isinstance(records, list):
            files_skipped.append({"file": str(path), "reason": "records are not a list"})
            continue
        files_read += 1
        summary, file_candidates, file_conflicts = audit_records(records, str(path))
        per_file[str(path)] = summary
        totals.update(summary)
        candidates.extend(file_candidates)
        conflicts.extend(file_conflicts)
    report = {
        "mode": "read_only_audit", "files_read": files_read,
        "files_skipped": files_skipped, "summary": dict(totals),
        "per_file_summary": per_file, "candidate_count": len(candidates),
        "candidates": candidates, "conflict_count": len(conflicts),
        "conflicts": conflicts,
        "note": "Suggestions only. No archive, review ledger, or seen-state file was modified.",
    }
    OUTPUT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Engine audit] Files read: {files_read}")
    print(f"[Engine audit] Files skipped: {len(files_skipped)}")
    print(f"[Engine audit] Records scanned: {totals['records']}")
    print(f"[Engine audit] Safe candidate records: {len(candidates)}")
    print(f"[Engine audit] Conflicting engine records: {len(conflicts)}")
    print(f"[Engine audit] Report: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
