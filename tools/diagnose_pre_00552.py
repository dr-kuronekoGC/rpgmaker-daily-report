#!/usr/bin/env python3
"""Read-only, single-item retrieval diagnostic for PRE-00552.

Uses the existing public-page retrieval and fallback logic. It does not modify
any ledger, decision history, archive, state file, Slack, or Notion data.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

from fetch_historical_review_bodies import USER_AGENT, fetch_item

PRE_ID = "PRE-00552"
LEDGER_PATH = Path("data/review/classification_review.json")
OUTPUT_PATH = Path("pre-00552-body-diagnostic.json")



def inspect_public_topic_js(session, script_sources: list[str]) -> dict:
    """Inspect the page's publicly linked Invision topic script without executing it."""
    script_url = next(
        (url for url in script_sources if "front_front_topic.js" in url),
        None,
    )
    result = {
        "attempted": bool(script_url),
        "url": script_url,
        "http_status": None,
        "content_type": "",
        "source_bytes": 0,
        "sha256": "",
        "request_api_counts": {},
        "endpoint_like_literals": [],
        "request_contexts": [],
        "error": "",
        "execution": "not_executed",
        "authentication": "none; public asset GET only",
    }
    if not script_url:
        result["error"] = "public topic script URL not found in page HTML"
        return result

    try:
        response = session.get(
            script_url,
            timeout=15,
            headers={"Accept": "text/javascript, application/javascript, */*"},
        )
        result["http_status"] = response.status_code
        result["content_type"] = response.headers.get("content-type", "")
        response.raise_for_status()
        source = response.text
    except Exception as exc:
        result["error"] = type(exc).__name__
        return result

    result["source_bytes"] = len(response.content)
    result["sha256"] = hashlib.sha256(response.content).hexdigest()

    patterns = {
        "fetch": r"\\bfetch\\s*\\(",
        "jquery_ajax": r"(?:\\$|jQuery)\\.ajax\\s*\\(",
        "ips_request": r"\\bips\\.(?:get|post|ajax)\\s*\\(",
        "xml_http_request": r"\\bXMLHttpRequest\\b",
        "axios": r"\\baxios\\.",
    }
    contexts = []
    for label, pattern in patterns.items():
        matches = list(re.finditer(pattern, source, re.IGNORECASE))
        result["request_api_counts"][label] = len(matches)
        for match in matches[:3]:
            start = max(0, match.start() - 160)
            end = min(len(source), match.end() + 240)
            contexts.append({
                "signal": label,
                "context": re.sub(r"\\s+", " ", source[start:end])[:420],
            })

    literals = re.findall(r"""["']([^"'\\r\\n]{1,240})["']""", source)
    needles = ("index.php", "controller=", "/api/", "ajax", "topic", "post", "content", "load", "comment")
    seen = set()
    for literal in literals:
        if any(needle in literal.lower() for needle in needles) and literal not in seen:
            seen.add(literal)
            result["endpoint_like_literals"].append(literal[:240])
            if len(result["endpoint_like_literals"]) >= 30:
                break

    result["request_contexts"] = contexts[:12]
    return result

def main() -> int:
    try:
        ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[PRE-00552 diagnostic] Cannot read ledger: {exc}", file=sys.stderr)
        return 2

    matches = [
        item for item in ledger.get("items", [])
        if isinstance(item, dict) and item.get("pre_id") == PRE_ID
    ]
    if len(matches) != 1:
        print(
            f"[PRE-00552 diagnostic] Expected exactly one {PRE_ID}; found {len(matches)}",
            file=sys.stderr,
        )
        return 2

    import requests

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    record = fetch_item(session, matches[0])
    html_diagnostics = record.get("html_diagnostics") or {}
    public_js_diagnostic = inspect_public_topic_js(
        session,
        html_diagnostics.get("script_sources") or [],
    )

    output = {
        "schema_version": 1,
        "audit_only": True,
        "pre_id": PRE_ID,
        "scope": "exactly one PRE item; public HTTP(S) retrieval only",
        "side_effects": "none; ledger, decisions, archive, state, Slack and Notion are not modified",
        "diagnostic": {
            key: record.get(key)
            for key in (
                "title", "source", "url", "historical_decision", "review_note",
                "retrieval_status", "retrieval_method", "http_status",
                "retrieval_error", "page_title", "page_description",
                "html_diagnostics", "requested_url", "final_url",
                "outbound_links", "source_tags",
            )
        },
        "body_text": record.get("body_text", ""),
        "public_js_diagnostic": public_js_diagnostic,
    }
    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    diagnostic = output["diagnostic"]
    html = diagnostic.get("html_diagnostics") or {}
    print(f"[PRE-00552 diagnostic] status={diagnostic.get('retrieval_status')}")
    print(f"[PRE-00552 diagnostic] method={diagnostic.get('retrieval_method')}")
    print(f"[PRE-00552 diagnostic] http_status={diagnostic.get('http_status')}")
    print(f"[PRE-00552 diagnostic] body_chars={len(output['body_text'])}")
    print(f"[PRE-00552 diagnostic] body_source={html.get('body_source')}")
    print(f"[PRE-00552 diagnostic] selector={html.get('body_selector_used')}")
    print(f"[PRE-00552 diagnostic] alternate_route_attempted={html.get('alternate_route_attempted')}")
    print(f"[PRE-00552 diagnostic] wayback_attempted={html.get('wayback_attempted')}")
    print(f"[PRE-00552 diagnostic] public_js_status={public_js_diagnostic.get('http_status')}")
    print(f"[PRE-00552 diagnostic] public_js_bytes={public_js_diagnostic.get('source_bytes')}")
    print(f"[PRE-00552 diagnostic] public_js_request_apis={public_js_diagnostic.get('request_api_counts')}")
    print(f"[PRE-00552 diagnostic] wrote={OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
