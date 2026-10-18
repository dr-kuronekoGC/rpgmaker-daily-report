#!/usr/bin/env python3
"""Synchronize the RPG Maker PRE review ledger with a Notion database.

GitHub's classification_review.json remains the durable record. Marking a row
"済" in Notion resolves an open PRE as reviewed; an existing GitHub decision
is never overwritten. Resolved rows remain in Notion but are hidden by the
"未確認一覧" view.
"""
from __future__ import annotations

import json
import os
import sys
import time
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

LEDGER_PATH = Path("data/review/classification_review.json")
NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
JST = timezone(timedelta(hours=9))
OPEN = "open"
RESOLVED = "resolved"
NOT_REVIEWED = "未確認"
REVIEWED = "済"
DEFAULT_PRIORITY = "通常"


def notion_request(method: str, path: str, token: str, payload: dict | None = None) -> dict:
    """Call Notion API with bounded retries for rate limits and transient errors."""
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        NOTION_API_BASE + path,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
    )
    for attempt in range(5):
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code in (429, 500, 502, 503, 504) and attempt < 4:
                retry_after = exc.headers.get("Retry-After", "")
                try:
                    delay = min(30, max(1, int(retry_after)))
                except ValueError:
                    delay = min(2 ** attempt, 16)
                print(f"[Notion sync] HTTP {exc.code}; retrying in {delay}s.")
                time.sleep(delay)
                continue
            raise RuntimeError(f"Notion API {method} {path} failed (HTTP {exc.code}): {detail}") from exc
        except (URLError, TimeoutError) as exc:
            if attempt < 4:
                delay = min(2 ** attempt, 16)
                print(f"[Notion sync] Network error; retrying in {delay}s.")
                time.sleep(delay)
                continue
            raise RuntimeError(f"Notion API request failed after retries: {exc}") from exc
    raise RuntimeError("Notion API request failed after retries.")


def title_value(prop: dict) -> str:
    pieces = prop.get("title", []) if isinstance(prop, dict) else []
    return "".join(piece.get("plain_text", "") for piece in pieces if isinstance(piece, dict))


def select_value(prop: dict) -> str:
    if not isinstance(prop, dict):
        return ""
    selected = prop.get("select")
    return selected.get("name", "") if isinstance(selected, dict) else ""


def url_value(prop: dict) -> str:
    return (prop.get("url") or "") if isinstance(prop, dict) else ""


def read_notion_pages(database_id: str, token: str) -> list[dict]:
    """Read every database page, following Notion's pagination cursor."""
    pages: list[dict] = []
    cursor = None
    while True:
        payload: dict = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        response = notion_request("POST", f"/databases/{database_id}/query", token, payload)
        pages.extend(response.get("results", []))
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
        if not cursor:
            raise RuntimeError("Notion reported more pages but did not provide next_cursor.")
    return pages


def page_properties(pre_id: str, url: str, priority: str, status: str) -> dict:
    if priority not in ("高", "通常", "低"):
        priority = DEFAULT_PRIORITY
    if status not in (NOT_REVIEWED, REVIEWED):
        status = NOT_REVIEWED
    return {
        "PRE番号": {"title": [{"text": {"content": pre_id}}]},
        "URL": {"url": url or None},
        "確認優先度": {"select": {"name": priority}},
        "確認状態": {"select": {"name": status}},
    }


def sync_state(queue: dict, notion_pages: list[dict], now: str | None = None) -> tuple[dict, list[tuple[str, dict]], list[dict], dict]:
    """Pure state reconciliation; returns updated ledger, page updates, creates, summary."""
    updated = deepcopy(queue)
    timestamp = now or datetime.now(JST).isoformat(timespec="seconds")
    ledger_items = updated.get("items")
    if not isinstance(ledger_items, list):
        raise ValueError('Ledger must contain an "items" list.')

    ledger_by_id: dict[str, dict] = {}
    for item in ledger_items:
        pre_id = item.get("pre_id") if isinstance(item, dict) else None
        if not isinstance(pre_id, str) or not pre_id:
            raise ValueError("Ledger contains an item without a valid pre_id.")
        if pre_id in ledger_by_id:
            raise ValueError(f"Duplicate PRE ID in ledger: {pre_id}")
        ledger_by_id[pre_id] = item

    notion_by_id: dict[str, dict] = {}
    for page in notion_pages:
        props = page.get("properties", {})
        pre_id = title_value(props.get("PRE番号", {}))
        if not pre_id:
            continue
        if pre_id in notion_by_id:
            raise ValueError(f"Duplicate PRE ID in Notion database: {pre_id}")
        notion_by_id[pre_id] = page

    page_updates: list[tuple[str, dict]] = []
    pages_to_create: list[dict] = []
    resolved_from_notion: list[str] = []
    marked_done_in_notion: list[str] = []
    created_ids: list[str] = []

    for item in ledger_items:
        pre_id = item["pre_id"]
        notion_page = notion_by_id.get(pre_id)
        if item.get("status") not in (OPEN, RESOLVED):
            continue

        if notion_page is None:
            initial_status = REVIEWED if item.get("status") == RESOLVED else NOT_REVIEWED
            properties = page_properties(pre_id, item.get("url", ""), DEFAULT_PRIORITY, initial_status)
            pages_to_create.append({"properties": properties})
            created_ids.append(pre_id)
            if initial_status == REVIEWED:
                marked_done_in_notion.append(pre_id)
            continue

        props = notion_page.get("properties", {})
        notion_status = select_value(props.get("確認状態", {}))
        notion_url = url_value(props.get("URL", {}))
        desired_status = REVIEWED if item.get("status") == RESOLVED else NOT_REVIEWED

        if item.get("status") == OPEN and notion_status == REVIEWED:
            item["status"] = RESOLVED
            item["decision"] = item.get("decision") or "reviewed_in_notion"
            item["resolved_at"] = item.get("resolved_at") or timestamp
            item["review_note"] = item.get("review_note") or (
                "Notionの確認状態を「済」に変更。詳細な分類判断は別途記録されていない。"
            )
            resolved_from_notion.append(pre_id)
            desired_status = REVIEWED

        new_properties = {}
        if notion_url != (item.get("url") or ""):
            new_properties["URL"] = {"url": item.get("url") or None}
        if notion_status != desired_status:
            new_properties["確認状態"] = {"select": {"name": desired_status}}
            if desired_status == REVIEWED:
                marked_done_in_notion.append(pre_id)
        if new_properties:
            page_updates.append((notion_page["id"], new_properties))

    summary = {
        "ledger_open": sum(item.get("status") == OPEN for item in ledger_items),
        "ledger_resolved": sum(item.get("status") == RESOLVED for item in ledger_items),
        "resolved_from_notion": resolved_from_notion,
        "marked_done_in_notion": marked_done_in_notion,
        "created_in_notion": created_ids,
        "page_updates": len(page_updates),
        "pages_to_create": len(pages_to_create),
    }
    return updated, page_updates, pages_to_create, summary


def write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    token = os.getenv("NOTION_API_KEY", "").strip()
    database_id = os.getenv("NOTION_DATABASE_ID", "").strip()
    if not token or not database_id:
        print("[Notion sync] Skipped: set NOTION_API_KEY and NOTION_DATABASE_ID in GitHub Actions secrets.")
        return 0
    if not LEDGER_PATH.exists():
        raise FileNotFoundError(f"Review ledger not found: {LEDGER_PATH}")

    queue = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    pages = read_notion_pages(database_id, token)
    updated, page_updates, pages_to_create, summary = sync_state(queue, pages)

    # Apply Notion mutations before saving the ledger. If a request fails, the
    # next run can safely retry; duplicate PRE IDs are rejected above.
    for page_id, properties in page_updates:
        notion_request("PATCH", f"/pages/{page_id}", token, {"properties": properties})
    for page in pages_to_create:
        notion_request("POST", "/pages", token, {**page, "parent": {"database_id": database_id}})

    if updated != queue:
        write_json_atomic(LEDGER_PATH, updated)

    print("[Notion sync] Complete.")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[Notion sync] ERROR: {exc}", file=sys.stderr)
        raise
