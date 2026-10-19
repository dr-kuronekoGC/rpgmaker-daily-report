#!/usr/bin/env python3
"""Audit URLs in the open review queue without modifying project data.

Only clear HTTP 404/410 responses are labelled dead-link candidates. Access
restrictions, rate limits, server errors and timeouts are kept separate so they
cannot accidentally cause a resource to be excluded.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup

LEDGER_PATH = Path("data/review/classification_review.json")
DECISIONS_PATH = Path("data/review/review_decisions.json")
OUTPUT_PATH = Path("review_link_audit.json")
USER_AGENT = "RPGMakerDailyReport-LinkAudit/1.0 (manual review utility)"
TIMEOUT = (5, 12)
MAX_WORKERS = 4

NOT_FOUND_TEXT = (
    "page not found", "this page doesn't exist", "this page does not exist",
    "content not found", "topic not found", "thread not found",
    "ページが見つかりません", "ページが存在しません", "削除されました",
    "страница не найдена", "страница не существует",
)


def audit_url(item: dict) -> dict:
    url = str(item.get("url") or "").strip()
    base = {
        "pre_id": item.get("pre_id"),
        "title": item.get("title"),
        "source": item.get("source"),
        "url": url,
        "description_available": bool(item.get("description") or item.get("body_text") or item.get("body")),
    }
    if not url.startswith(("http://", "https://")):
        return {**base, "link_status": "invalid_url", "status_code": None, "final_url": None, "page_title": None, "page_signal": None, "error": "missing_or_invalid_http_url"}

    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
            allow_redirects=True,
        )
        status = response.status_code
        content_type = response.headers.get("Content-Type", "")
        page_title = None
        page_signal = None
        if "text/html" in content_type.lower() and response.text:
            soup = BeautifulSoup(response.text[:500_000], "html.parser")
            if soup.title:
                page_title = soup.title.get_text(" ", strip=True)[:250]
            text = soup.get_text(" ", strip=True).lower()[:200_000]
            matched = next((phrase for phrase in NOT_FOUND_TEXT if phrase in text), None)
            if matched:
                page_signal = "not_found_text:" + matched

        if status in (404, 410):
            link_status = "dead_link_candidate"
        elif status in (403, 429):
            link_status = "blocked_or_rate_limited"
        elif status >= 500:
            link_status = "server_error_retry"
        elif status >= 400:
            link_status = "http_error_review"
        elif page_signal:
            link_status = "page_may_be_deleted"
        else:
            link_status = "reachable"

        return {
            **base,
            "link_status": link_status,
            "status_code": status,
            "final_url": response.url,
            "page_title": page_title,
            "page_signal": page_signal,
            "content_type": content_type,
            "error": None,
        }
    except requests.RequestException as exc:
        return {
            **base,
            "link_status": "connection_error_unconfirmed",
            "status_code": None,
            "final_url": None,
            "page_title": None,
            "page_signal": None,
            "error": type(exc).__name__,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit open review links; optionally resolve confirmed dead links.")
    parser.add_argument(
        "--apply-dead-links",
        action="store_true",
        help="Resolve only confirmed HTTP 404/410 links and record not_applicable decisions.",
    )
    args = parser.parse_args()

    try:
        ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[Link audit] Cannot read review ledger: {exc}")
        return 2

    items = ledger.get("items") if isinstance(ledger, dict) else None
    if not isinstance(items, list):
        print("[Link audit] Invalid review ledger")
        return 2

    open_items = [
        item for item in items
        if isinstance(item, dict) and item.get("status") == "open" and item.get("url")
    ]
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(audit_url, item) for item in open_items]
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda row: row.get("pre_id") or "")
    counts = {}
    for row in results:
        status = row["link_status"]
        counts[status] = counts.get(status, 0) + 1

    payload = {
        "schema_version": 1,
        "audit_only": True,
        "source_ledger": str(LEDGER_PATH),
        "checked_count": len(results),
        "status_counts": dict(sorted(counts.items())),
        "important_note": (
            "This audit does not change the review queue. Only HTTP 404/410 are "
            "dead-link candidates. 403/429, server errors, timeouts, and pages "
            "that merely look like not-found pages are not automatic exclusions. "
            "A reachable page does not prove that a usable asset is available."
        ),
        "items": results,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.apply_dead_links:
        try:
            decisions_data = json.loads(DECISIONS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[Link audit] Cannot read decision ledger: {exc}")
            return 2
        decisions = decisions_data.get("decisions")
        if not isinstance(decisions, list):
            print("[Link audit] Invalid decision ledger")
            return 2

        by_id = {row.get("pre_id"): row for row in results}
        known_decisions = {row.get("pre_id") for row in decisions if isinstance(row, dict)}
        now = datetime.now(timezone.utc).isoformat()
        applied = 0
        for item in items:
            if not isinstance(item, dict) or item.get("status") != "open":
                continue
            audit = by_id.get(item.get("pre_id"))
            if not audit or audit.get("link_status") != "dead_link_candidate":
                continue
            note = (
                f"自動リンク確認でHTTP {audit.get('status_code')}を確認。"
                "404/410の明確なリンク切れのため、利用可能な配布元を確認できず対象外。"
            )
            item["status"] = "resolved"
            item["decision"] = "not_applicable"
            item["resolved_at"] = now
            item["review_note"] = note
            if item.get("pre_id") not in known_decisions:
                decisions.append({
                    "pre_id": item.get("pre_id"),
                    "decision": "not_applicable",
                    "note": note,
                })
                known_decisions.add(item.get("pre_id"))
            applied += 1

        LEDGER_PATH.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        DECISIONS_PATH.write_text(json.dumps(decisions_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[Link audit] Applied confirmed dead-link exclusions: {applied}")
        print("[Link audit] 403/429, 5xx, timeouts and ambiguous not-found page text remain open.")

    print(f"[Link audit] Checked open review URLs: {len(results)}")
    print(f"[Link audit] Status counts: {dict(sorted(counts.items()))}")
    for row in results:
        if row["link_status"] in {"dead_link_candidate", "page_may_be_deleted", "connection_error_unconfirmed"}:
            print(f"[Link audit candidate] {row['pre_id']} | {row['link_status']} | HTTP {row['status_code']} | {row['title']} | {row['url']}")
    if not args.apply_dead_links:
        print("[Link audit] Audit only; no review decisions or data were changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
