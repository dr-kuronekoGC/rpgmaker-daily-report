#!/usr/bin/env python3
"""Validate that generated archive previews change only the engine field.

The preview files are produced by tools/backfill_engine_metadata.py. This script
validates every monthly archive before copying any preview over its source.
"""
import json
from pathlib import Path

ARCHIVE_DIR = Path("data/archive")
PREVIEW_DIR = Path("engine_backfill_preview")


def _records(data, label):
    if isinstance(data, list):
        return data, None
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        return data["items"], "items"
    raise ValueError(f"{label}: expected a list or an object with an items list")


def validate_engine_only_change(original, preview, source_file="archive"):
    """Raise ValueError unless the only semantic changes are record engine values."""
    original_records, original_key = _records(original, source_file)
    preview_records, preview_key = _records(preview, f"{source_file} preview")
    if original_key != preview_key or len(original_records) != len(preview_records):
        raise ValueError(f"{source_file}: archive structure or record count changed")

    if isinstance(original, dict):
        if set(original) != set(preview):
            raise ValueError(f"{source_file}: top-level keys changed")
        for key in original:
            if key != "items" and original[key] != preview[key]:
                raise ValueError(f"{source_file}: non-record metadata changed at {key!r}")

    changed_records = 0
    for index, (old_item, new_item) in enumerate(zip(original_records, preview_records)):
        if not isinstance(old_item, dict) or not isinstance(new_item, dict):
            if old_item != new_item:
                raise ValueError(f"{source_file}: non-object record changed at index {index}")
            continue
        expected = dict(old_item)
        if "engine" in new_item:
            expected["engine"] = new_item["engine"]
        else:
            expected.pop("engine", None)
        if expected != new_item:
            raise ValueError(
                f"{source_file}: fields other than engine changed at record index {index} "
                f"({old_item.get('internal_id') or old_item.get('title')})"
            )
        if old_item.get("engine") != new_item.get("engine"):
            changed_records += 1
    return changed_records


def prepare_preview_copies(archive_dir=ARCHIVE_DIR, preview_dir=PREVIEW_DIR):
    """Validate all monthly previews, then copy only validated archive previews."""
    plans = []
    for source_path in sorted(Path(archive_dir).glob("????-??.json")):
        preview_path = Path(preview_dir) / source_path.name
        if not preview_path.is_file():
            raise ValueError(f"Missing preview for {source_path}: {preview_path}")
        with source_path.open("r", encoding="utf-8") as handle:
            original = json.load(handle)
        with preview_path.open("r", encoding="utf-8") as handle:
            preview = json.load(handle)
        changed = validate_engine_only_change(original, preview, str(source_path))
        plans.append((source_path, preview_path, changed))

    if not plans:
        raise ValueError(f"No monthly archive files found in {archive_dir}")

    for source_path, preview_path, _ in plans:
        source_path.write_bytes(preview_path.read_bytes())

    total = sum(changed for _, _, changed in plans)
    print(f"[Engine backfill PR] Monthly archives validated: {len(plans)}")
    print(f"[Engine backfill PR] Records with engine changes: {total}")
    print("[Engine backfill PR] Validation passed: no non-engine fields changed")
    return total


if __name__ == "__main__":
    prepare_preview_copies()
