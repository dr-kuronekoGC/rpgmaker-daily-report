#!/usr/bin/env python3
"""Safely import explicit human decisions into the classification review ledger.

Dry-run is the default. Pass --apply to write changes to the ledger.
The decisions file is intentionally not deleted or rewritten.
"""
import argparse
import json
import os
import re
import tempfile
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_LEDGER = Path("data/review/classification_review.json")
DEFAULT_DECISIONS = Path("data/review/review_decisions.json")
PRE_ID_PATTERN = re.compile(r"^PRE-\\d{5}$")
JST = timezone(timedelta(hours=9))


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_decisions(payload, queue):
    """Validate the whole batch before changing any record."""
    if not isinstance(payload, dict) or not isinstance(payload.get("decisions"), list):
        raise ValueError('Decision file must be an object containing a "decisions" list.')

    items = queue.get("items")
    if not isinstance(items, list):
        raise ValueError('Ledger must contain an "items" list.')

    by_pre_id = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Ledger contains a non-object item.")
        pre_id = item.get("pre_id")
        if not isinstance(pre_id, str) or not pre_id:
            raise ValueError("Ledger item is missing a valid pre_id.")
        if pre_id in by_pre_id:
            raise ValueError(f"Ledger contains duplicate PRE ID: {pre_id}")
        by_pre_id[pre_id] = item

    normalized = []
    seen_ids = set()
    for index, entry in enumerate(payload["decisions"], start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"Decision #{index} must be an object.")
        pre_id = entry.get("pre_id")
        decision = entry.get("decision")
        note = entry.get("note", "")

        if not isinstance(pre_id, str) or not PRE_ID_PATTERN.fullmatch(pre_id):
            raise ValueError(f"Decision #{index} has an invalid pre_id.")
        if pre_id in seen_ids:
            raise ValueError(f"Duplicate decision for {pre_id}.")
        seen_ids.add(pre_id)

        if not isinstance(decision, str) or not decision.strip() or len(decision.strip()) > 80:
            raise ValueError(f"{pre_id}: decision must be a non-empty string of at most 80 characters.")
        if not isinstance(note, str) or len(note) > 1000:
            raise ValueError(f"{pre_id}: note must be a string of at most 1000 characters.")
        if pre_id not in by_pre_id:
            raise ValueError(f"{pre_id} does not exist in the ledger.")

        current = by_pre_id[pre_id]
        if current.get("status") == "resolved":
            same_decision = current.get("decision") == decision.strip()
            same_note = (current.get("review_note") or "") == note.strip()
            if same_decision and same_note:
                normalized.append({
                    "pre_id": pre_id, "decision": decision.strip(),
                    "note": note.strip(), "action": "already_applied",
                })
                continue
            raise ValueError(f"{pre_id} is already resolved with a different decision; refusing to overwrite it.")
        if current.get("status") != "open":
            raise ValueError(f"{pre_id} has unsupported status {current.get('status')!r}.")

        normalized.append({
            "pre_id": pre_id, "decision": decision.strip(),
            "note": note.strip(), "action": "resolve",
        })

    return normalized, by_pre_id


def apply_decisions(queue, payload, resolved_at=None):
    """Return an updated queue and a summary; never write files here."""
    normalized, by_pre_id = validate_decisions(payload, queue)
    updated = deepcopy(queue)
    updated_by_id = {item["pre_id"]: item for item in updated["items"]}
    timestamp = resolved_at or datetime.now(JST).isoformat(timespec="seconds")
    applied = []

    for entry in normalized:
        if entry["action"] == "already_applied":
            continue
        item = updated_by_id[entry["pre_id"]]
        item["status"] = "resolved"
        item["decision"] = entry["decision"]
        item["resolved_at"] = timestamp
        item["review_note"] = entry["note"] or None
        applied.append(entry["pre_id"])

    return updated, {
        "requested": len(normalized),
        "applied": len(applied),
        "already_applied": sum(e["action"] == "already_applied" for e in normalized),
        "resolved_pre_ids": applied,
    }


def write_json_atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\\n")
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument(
        "--apply", action="store_true",
        help="write validated decisions to the ledger (default: dry-run only)",
    )
    args = parser.parse_args()

    if not args.decisions.exists():
        parser.error(f"Decision file not found: {args.decisions}")

    queue = load_json(args.ledger)
    payload = load_json(args.decisions)
    updated, summary = apply_decisions(queue, payload)

    print(f"[Review decisions] Requested: {summary['requested']}")
    print(f"[Review decisions] To resolve: {summary['applied']}")
    print(f"[Review decisions] Already applied: {summary['already_applied']}")
    if summary["resolved_pre_ids"]:
        print("[Review decisions] PRE IDs:", ", ".join(summary["resolved_pre_ids"]))

    if not args.apply:
        print("[Review decisions] DRY RUN: ledger was not changed. Re-run with --apply to save.")
        return

    write_json_atomic(args.ledger, updated)
    print(f"[Review decisions] Updated ledger: {args.ledger}")


if __name__ == "__main__":
    main()
