#!/usr/bin/env python3
"""Read-only audit of engine values that may be recoverable from archived metadata.

This script never edits archive files. It writes a report suitable for inspection
before any historical record is changed.
"""
import json
from collections import Counter
from pathlib import Path

from asset_metadata import detect_engine


ARCHIVE_DIR = Path("data/archive")
OUTPUT_FILE = Path("engine_backfill_audit.json")

SPECIFIC_ENGINES = {
    "MZ", "MV", "MV Trinity", "VX Ace", "VX", "XP",
    "2003", "2000", "95", "U2U", "UNITE",
}


def _as_engine_list(value):
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item]
    return []


def audit_records(records, source_file=""):
    summary = Counter()
    candidates = []

    for item in records:
        if not isinstance(item, dict):
            summary["invalid_records"] += 1
            continue

        summary["records"] += 1
        old_engines = _as_engine_list(item.get("engine"))
        if not old_engines or "不明" in old_engines:
            summary["records_with_unknown_engine"] += 1
        if "その他RPG Maker" in old_engines:
            summary["records_with_generic_rpg_maker"] += 1

        proposed = detect_engine(item)
        concrete = [engine for engine in proposed if engine in SPECIFIC_ENGINES]
        old_concrete = [engine for engine in old_engines if engine in SPECIFIC_ENGINES]
        additions = [engine for engine in concrete if engine not in old_concrete]

        if not additions:
            continue

        summary["candidate_records"] += 1
        for engine in additions:
            summary["candidate_engine_" + engine.replace(" ", "_")] += 1

        evidence_fields = []
        for field in ("title", "description", "body_text", "post_body", "source_tags", "tags", "url"):
            value = item.get(field)
            if isinstance(value, str) and value.strip():
                evidence_fields.append({"field": field, "text": value.strip()[:500]})
            elif isinstance(value, list) and value:
                evidence_fields.append({"field": field, "text": ", ".join(str(x) for x in value[:20])[:500]})

        candidates.append({
            "source_file": source_file,
            "internal_id": item.get("internal_id"),
            "title": item.get("title"),
            "url": item.get("url"),
            "source": item.get("source"),
            "collector": item.get("collector"),
            "old_engine": old_engines,
            "proposed_engine": proposed,
            "new_specific_engines": additions,
            "evidence": evidence_fields,
        })

    return dict(summary), candidates


def main():
    totals = Counter()
    candidates = []
    files_read = 0
    files_skipped = []
    per_file_summary = {}

    # Only monthly archive files are data records; exclude indexes or other JSON metadata.
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
        summary, file_candidates = audit_records(records, source_file=str(path))
        per_file_summary[str(path)] = summary
        totals.update(summary)
        candidates.extend(file_candidates)

    report = {
        "mode": "read_only_audit",
        "files_read": files_read,
        "files_skipped": files_skipped,
        "summary": dict(totals),
        "per_file_summary": per_file_summary,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "note": "Suggestions only. No archive, review ledger, or seen-state file was modified.",
    }

    OUTPUT_FILE.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[Engine audit] Files read: {files_read}")
    print(f"[Engine audit] Files skipped: {len(files_skipped)}")
    print(f"[Engine audit] Records scanned: {totals['records']}")
    print(f"[Engine audit] Unknown-engine records: {totals['records_with_unknown_engine']}")
    print(f"[Engine audit] Candidate records: {len(candidates)}")
    print(f"[Engine audit] Report: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
