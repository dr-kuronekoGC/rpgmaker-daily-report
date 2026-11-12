#!/usr/bin/env python3
"""Read-only preview of explicitly approved PRE-to-Archive metadata patches.

This tool never writes files. It requires a proposal manifest with exact identity,
expected current values, desired values, and human-confirmation evidence.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PRE_ID_RE = re.compile(r"^PRE-\d{5}$")
DEFAULT_ARCHIVE_DIR = Path("data/archive")
DEFAULT_LEDGER = Path("data/review/classification_review.json")
DEFAULT_DECISIONS = Path("data/review/review_decisions.json")
DEFAULT_MANIFEST = Path("data/review/archive_patch_proposals.json")
ALLOWED_FIELDS = {
    "content_type",
    "asset_type",
    "development_info_type",
    "tags",
    "engine",
    "supported_platforms",
    "engine_relevant",
    "classification_status",
    "classification_confidence",
    "classification_note",
}


def load_json(path: Path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_archive_records(archive_dir: Path) -> list[dict]:
    """Load month archives only; never load or modify the override index."""
    records = []
    for path in sorted(archive_dir.glob("20??-??.json")):
        payload = load_json(path)
        if not isinstance(payload, list):
            raise ValueError(f"{path}: archive must be a JSON list.")
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError(f"{path}: archive contains a non-object record.")
            records.append(item)
    return records


def _index_unique(items: list[dict], key: str, value: str, label: str) -> dict:
    matches = [item for item in items if item.get(key) == value]
    if len(matches) != 1:
        raise ValueError(
            f"{label}: expected exactly one match for {key}={value!r}; found {len(matches)}."
        )
    return matches[0]


def _validate_patch_shape(patch: dict, index: int) -> None:
    prefix = f"Patch #{index}"
    pre_id = patch.get("pre_id")
    if not isinstance(pre_id, str) or not PRE_ID_RE.fullmatch(pre_id):
        raise ValueError(f"{prefix}: invalid pre_id.")
    for field in ("internal_id", "source_url"):
        if not isinstance(patch.get(field), str) or not patch[field].strip():
            raise ValueError(f"{prefix}: {field} is required.")
    expected = patch.get("expected")
    desired = patch.get("set")
    if not isinstance(expected, dict) or not isinstance(desired, dict) or not desired:
        raise ValueError(f"{prefix}: expected and non-empty set objects are required.")
    if set(expected) != set(desired):
        raise ValueError(f"{prefix}: expected and set must contain exactly the same fields.")
    unknown = (set(expected) | set(desired)) - ALLOWED_FIELDS
    if unknown:
        raise ValueError(f"{prefix}: unsupported fields: {', '.join(sorted(unknown))}.")
    evidence = patch.get("evidence")
    if not isinstance(evidence, dict) or evidence.get("kind") != "user_confirmation":
        raise ValueError(f"{prefix}: explicit user_confirmation evidence is required.")
    if not isinstance(evidence.get("note"), str) or not evidence["note"].strip():
        raise ValueError(f"{prefix}: evidence note is required.")


def preview_patches(
    manifest: dict,
    archive_records: list[dict],
    review_ledger: dict,
    review_decisions: dict,
) -> list[dict]:
    """Validate every proposal and return a diff; never mutate input objects."""
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValueError("Manifest schema_version must be 1.")
    patches = manifest.get("patches")
    if not isinstance(patches, list):
        raise ValueError('Manifest must contain a "patches" list.')
    ledger_items = review_ledger.get("items")
    decisions = review_decisions.get("decisions")
    if not isinstance(ledger_items, list) or not isinstance(decisions, list):
        raise ValueError("Review ledger or review decisions has an invalid structure.")

    seen_pre_ids = set()
    results = []
    for index, patch in enumerate(patches, start=1):
        if not isinstance(patch, dict):
            raise ValueError(f"Patch #{index} must be an object.")
        _validate_patch_shape(patch, index)
        pre_id = patch["pre_id"]
        if pre_id in seen_pre_ids:
            raise ValueError(f"Duplicate patch for {pre_id}.")
        seen_pre_ids.add(pre_id)

        ledger_item = _index_unique(ledger_items, "pre_id", pre_id, "PRE ledger")
        if ledger_item.get("status") != "resolved" or ledger_item.get("decision") != "confirmed":
            raise ValueError(f"{pre_id}: PRE ledger is not resolved/confirmed.")
        if ledger_item.get("internal_id") != patch["internal_id"]:
            raise ValueError(f"{pre_id}: internal_id does not match the PRE ledger.")
        if ledger_item.get("url") != patch["source_url"]:
            raise ValueError(f"{pre_id}: source_url does not match the PRE ledger.")

        decision_item = _index_unique(decisions, "pre_id", pre_id, "Review decisions")
        if decision_item.get("decision") != "confirmed":
            raise ValueError(f"{pre_id}: review_decisions does not confirm this item.")

        archive_by_pre = _index_unique(archive_records, "pre_id", pre_id, "Archive")
        archive_by_internal = _index_unique(
            archive_records, "internal_id", patch["internal_id"], "Archive"
        )
        if archive_by_pre is not archive_by_internal:
            raise ValueError(f"{pre_id}: PRE ID and internal_id point to different Archive records.")
        if archive_by_pre.get("url") != patch["source_url"]:
            raise ValueError(f"{pre_id}: source_url does not match the Archive record.")

        current = {field: archive_by_pre.get(field) for field in patch["expected"]}
        if current != patch["expected"]:
            raise ValueError(
                f"{pre_id}: expected-value conflict; expected={patch['expected']!r}, "
                f"current={current!r}."
            )
        already_matches = all(
            archive_by_pre.get(field) == value for field, value in patch["set"].items()
        )
        results.append({
            "pre_id": pre_id,
            "internal_id": patch["internal_id"],
            "status": "already_matches" if already_matches else "ready_for_review",
            "changes": [
                {
                    "field": field,
                    "before": archive_by_pre.get(field),
                    "after": value,
                }
                for field, value in patch["set"].items()
                if archive_by_pre.get(field) != value
            ],
            "evidence": patch["evidence"],
            "schema_version": manifest.get("target_schema_version"),
        })
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--archive-dir", type=Path, default=DEFAULT_ARCHIVE_DIR)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    archive_records = load_archive_records(args.archive_dir)
    results = preview_patches(
        manifest, archive_records, load_json(args.ledger), load_json(args.decisions)
    )
    print(json.dumps({
        "mode": "read_only_preview",
        "archive_records_loaded": len(archive_records),
        "proposal_count": len(results),
        "results": results,
        "writes_performed": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
