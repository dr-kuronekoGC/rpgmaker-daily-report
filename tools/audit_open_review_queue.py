#!/usr/bin/env python3
"""Re-evaluate open classification reviews using stored evidence only.

Audit-only: this script never resolves queue entries or changes the review
ledger, archive, seen state, pending state, or human decisions.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from asset_metadata import build_asset_metadata

LEDGER_PATH = Path("data/review/classification_review.json")
OUTPUT_PATH = Path("open_review_audit.json")


def audit_item(item: dict) -> dict:
    # Reuse the current runtime classifier on a copy of the stored review
    # record. Missing page bodies remain missing; they are not treated as
    # evidence that an item is or is not a resource.
    try:
        enriched = build_asset_metadata(item)
        intent = enriched.get("resource_intent", "uncertain")
        confidence = enriched.get("resource_intent_confidence", "unknown")
        evidence = enriched.get("resource_intent_evidence", [])
        if intent == "not_resource":
            suggestion = "candidate_exclude"
        elif intent == "resource_candidate":
            suggestion = "candidate_resource"
        else:
            suggestion = "keep_manual_review"
        error = None
    except Exception as exc:  # one malformed historical record must not stop the audit
        intent = "uncertain"
        confidence = "unknown"
        evidence = []
        suggestion = "keep_manual_review"
        error = type(exc).__name__

    return {
        "pre_id": item.get("pre_id"),
        "internal_id": item.get("internal_id"),
        "source": item.get("source"),
        "title": item.get("title"),
        "url": item.get("url"),
        "category": item.get("category"),
        "stored_description_available": bool(
            item.get("description") or item.get("body_text") or item.get("body")
        ),
        "audit_intent": intent,
        "audit_confidence": confidence,
        "audit_evidence": evidence,
        "suggestion": suggestion,
        "error": error,
        "warning": (
            "Candidate only; not an approved human decision. "
            "Stored evidence may be incomplete."
        ),
    }


def main() -> int:
    try:
        ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[Open review audit] Cannot read ledger: {exc}")
        return 2

    items = ledger.get("items") if isinstance(ledger, dict) else None
    if not isinstance(items, list):
        print("[Open review audit] Invalid ledger format")
        return 2

    open_items = [
        item for item in items
        if isinstance(item, dict) and item.get("status") == "open"
    ]
    audited = [audit_item(item) for item in open_items]
    counts = Counter(record["suggestion"] for record in audited)
    source_counts = Counter(
        (record["source"] or "Unknown", record["suggestion"])
        for record in audited
    )

    output = {
        "schema_version": 1,
        "audit_only": True,
        "source_ledger": str(LEDGER_PATH),
        "open_item_count": len(open_items),
        "suggestion_counts": dict(sorted(counts.items())),
        "source_suggestion_counts": [
            {"source": source, "suggestion": suggestion, "count": count}
            for (source, suggestion), count in sorted(source_counts.items())
        ],
        "note": (
            "Suggestions are for re-review only. No review item is resolved "
            "or changed, and incomplete page text is not treated as exclusion evidence."
        ),
        "items": audited,
    }
    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[Open review audit] Open items: {len(open_items)}")
    print(f"[Open review audit] Suggestions: {dict(sorted(counts.items()))}")
    for row in audited:
        if row["suggestion"] != "keep_manual_review":
            print(
                f"[Open review candidate] {row['pre_id']} | {row['suggestion']} | "
                f"{row['source']} | {row['title']} | {row['url']}"
            )
    print("[Open review audit] Audit only; review ledger unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
