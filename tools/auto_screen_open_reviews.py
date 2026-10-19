#!/usr/bin/env python3
"""Conservatively resolve only high-confidence non-resource review records.

This script is intentionally stricter than a classifier:
- HTTP 404/410 can establish that the stored page is unavailable.
- Clear direct profile URLs are not individual deliverables.
- Explicit requests/discussions/showcases are excluded only when the page has
  no strong release/download evidence.
- 403/429/5xx/timeouts and parse failures are NEVER treated as dead links.
Ambiguous records remain open for human review.
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import fetch_historical_review_bodies as fetcher
from asset_metadata import build_asset_metadata

LEDGER_PATH = Path("data/review/classification_review.json")
LOG_PATH = Path("data/review/auto_screen_log.json")
JST = timezone(timedelta(hours=9))

# Avoid long hangs on sites that are currently blocking or timing out.
fetcher.TIMEOUT = 8
fetcher.PAUSE_SECONDS = 0.15

RESOLVED_MARKER_RE = re.compile(r"\b(?:solved|resolved|filled|answered|completed)\b", re.I)
REQUEST_RE = re.compile(
    r"\b(?:looking for|searching for|request(?:ing)?|need(?:ing)?|"
    r"can anyone (?:make|share|provide|create)|anyone have|gimme|give me|"
    r"need help finding|does anyone have|wanted)\b",
    re.I,
)
DISCUSSION_RE = re.compile(
    r"\b(?:discussion|discuss|what do you think|which is better|"
    r"how do i|how can i|why does|is there a way|question|help with)\b",
    re.I,
)
SHOWCASE_RE = re.compile(
    r"\b(?:showcase|my game|my project|my works|work in progress|\bwip\b|"
    r"development process|making of|screenshots?|gameplay video|mapping showcase)\b",
    re.I,
)
NO_DELIVERABLE_RE = re.compile(
    r"\b(?:not a resource|no download|not available for download|"
    r"not for download|just (?:a )?(?:screenshot|preview|showcase)|"
    r"only a preview|not sharing (?:this|these|it)|not a release|"
    r"no files? (?:attached|provided)|made only for my own game)\b",
    re.I,
)
POSITIVE_RELEASE_RE = re.compile(
    r"\b(?:download(?:able)?|download link|released?|release page|"
    r"resource pack|asset pack|free to use|available for use|"
    r"get it here|mediafire|mega\.nz|dropbox|google drive|"
    r"itch\.io|github\.com|\.zip\b|\.rar\b|\.7z\b|"
    r"\.ogg\b|\.mp3\b|\.wav\b|\.js\b)",
    re.I,
)
ASSET_WORD_RE = re.compile(
    r"\b(?:sprite|sprites|charset|battler|tileset|tile set|icon pack|"
    r"resource|asset|plugin|script|bgm|bgs|sound effect|music pack|"
    r"animation sheet|sound pack|tool)\b",
    re.I,
)
COPYRIGHT_WARNING_RE = re.compile(
    r"\b(?:pirate|ripped from|ripped music|dragon ball|pokemon|pokémon|naruto|star ocean)\b",
    re.I,
)


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def is_direct_profile(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/").lower()
    host = (parsed.hostname or "").lower()
    if re.search(r"/(?:forum/)?(?:user|users|profile|profiles|members)/[^/]+$", path):
        return True
    # DeviantArt artist landing pages are profiles; individual works use /art/.
    if host.endswith("deviantart.com") and path.count("/") == 1 and "/art/" not in path:
        return True
    # itch.io creator landing pages, not individual project pages.
    if host.endswith(".itch.io") and path in {"", "/"}:
        return True
    return False


def classify_page(item: dict, page: dict) -> tuple[str, str] | None:
    url = clean(item.get("url"))
    title = clean(page.get("page_title") or item.get("title"))
    body = clean(page.get("body_text") or page.get("page_description"))
    combined = f"{title}\n{body}"
    status = page.get("http_status")
    retrieval = page.get("retrieval_status")

    if status in {404, 410}:
        return ("not_applicable", f"保存されたURLがHTTP {status}を返し、現在ページを取得できない")
    if is_direct_profile(url):
        return ("not_applicable", "個別の素材・配布物ではなく、ユーザープロフィールへの直リンク")
    if retrieval != "body_found" or not body:
        # A blank/blocked response is not evidence of absence.
        return None

    positive_release = bool(POSITIVE_RELEASE_RE.search(combined))
    resolved_marker = bool(RESOLVED_MARKER_RE.search(title))
    copyright_warning = bool(COPYRIGHT_WARNING_RE.search(combined))

    if copyright_warning and not positive_release:
        # Avoid generic franchise-word filtering; only clear piracy/ripped wording
        # is an exclusion. Franchise names alone are insufficient.
        explicit_piracy = bool(re.search(r"\b(?:pirate|ripped from|ripped music)\b", combined, re.I))
        if explicit_piracy:
            return ("exclude", "海賊版・既存作品からのリッピングを明示する投稿で、公開対象の独自素材として扱えない")

    if NO_DELIVERABLE_RE.search(combined) and not positive_release:
        return ("not_applicable", "本文に素材配布ではない／ダウンロード不可／プレビューのみと明記されている")

    # A solved/filled thread may contain a useful answer or an attached asset.
    if resolved_marker:
        return None

    # Requests for a resource are excluded only when the post itself contains
    # no release/download evidence. Ambiguous threads remain open.
    request_signal = bool(REQUEST_RE.search(title) or REQUEST_RE.search(body[:1800]))
    if request_signal and not positive_release:
        return ("not_applicable", "素材・プラグイン等を求める依頼投稿で、取得可能な配布物の記載を確認できない")

    # Generic discussion/question/showcase language alone is too weak.
    # Require explicit non-deliverable context and no release evidence.
    non_asset_context = bool(DISCUSSION_RE.search(title) or SHOWCASE_RE.search(title))
    explicit_no_release = bool(re.search(
        r"\b(?:just asking|question only|discussion only|not released|"
        r"no files attached|not sharing|for feedback only|showing my game only)\b",
        body[:2200], re.I
    ))
    if non_asset_context and explicit_no_release and not positive_release:
        return ("not_applicable", "質問・議論・作品紹介のみで、本文にも配布物がないことが明示されている")

    # Reuse the project's established resource-intent classifier against
    # the freshly fetched page text. Only act on explicit high-confidence
    # non-resource results, or medium-confidence question/request/showcase
    # signals; positive distribution evidence always keeps the item open.
    candidate = dict(item)
    candidate["body_text"] = body
    candidate["description"] = clean(page.get("page_description"))
    try:
        triage = build_asset_metadata(candidate)
        intent = triage.get("resource_intent")
        confidence = triage.get("resource_intent_confidence")
        evidence = triage.get("resource_intent_evidence") or []
        signals = {
            entry.get("signal")
            for entry in evidence
            if isinstance(entry, dict)
        }
        if intent == "not_resource" and not positive_release:
            if confidence == "high":
                return ("not_applicable", "既存の素材意図分類器が高確度で素材・配布物ではないと判定")
            if confidence == "medium" and signals.intersection({
                "question_or_showcase_title",
                "request_or_question_slug",
                "non_resource_category",
            }):
                return ("not_applicable", "既存の素材意図分類器が質問・依頼・作品紹介を検出し、本文にも配布根拠がない")
    except Exception:
        # A classifier error is not evidence that an item should be excluded.
        pass

    # Copyrighted franchise names without an explicit piracy indicator are
    # intentionally not auto-excluded.
    return None


def main() -> int:
    try:
        ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[Auto screen] Cannot read ledger: {exc}", file=sys.stderr)
        return 2

    items = ledger.get("items")
    if not isinstance(items, list):
        print("[Auto screen] Invalid review ledger: expected items list", file=sys.stderr)
        return 2

    open_items = [x for x in items if isinstance(x, dict) and x.get("status") == "open"]
    session = fetcher.requests.Session()
    session.headers.update({"User-Agent": fetcher.USER_AGENT})
    now = datetime.now(JST).isoformat(timespec="seconds")
    log = []
    resolved = []

    for index, item in enumerate(open_items, start=1):
        page = fetcher.fetch_item(session, item)
        # Discourse's JSON endpoint can fail while the ordinary topic page
        # still works. Verify the original URL before treating JSON 404/410
        # as a dead link.
        if page.get("retrieval_method") == "discourse_json" and page.get("http_status") in {404, 410}:
            try:
                html_page = fetcher.parse_html(session, clean(item.get("url")))
                page.update(html_page)
                if page.get("body_text") or page.get("page_description"):
                    page["retrieval_status"] = "body_found"
                elif page.get("http_status") == 200:
                    page["retrieval_status"] = "page_loaded_no_body"
            except fetcher.requests.HTTPError as exc:
                actual_status = exc.response.status_code if exc.response is not None else None
                if actual_status not in {404, 410}:
                    page["http_status"] = actual_status
                    page["retrieval_status"] = "unavailable"
            except fetcher.requests.RequestException:
                # An unverified HTML retry is not proof that the link is dead.
                page["http_status"] = None
                page["retrieval_status"] = "unavailable"
        outcome = classify_page(item, page)
        print(
            f"[Auto screen] {index}/{len(open_items)} {item.get('pre_id')} "
            f"http={page.get('http_status')} retrieval={page.get('retrieval_status')} "
            f"decision={outcome[0] if outcome else 'keep_open'}"
        )
        if outcome:
            decision, reason = outcome
            evidence = {
                "method": "automated_screening_v1",
                "checked_at": now,
                "http_status": page.get("http_status"),
                "retrieval_status": page.get("retrieval_status"),
                "page_title": clean(page.get("page_title"))[:300],
                "reason": reason,
            }
            item["status"] = "resolved"
            item["decision"] = decision
            item["resolved_at"] = now
            item["review_note"] = f"自動スクリーニング（高確度）: {reason}。取得状況: HTTP {page.get('http_status') or '不明'} / {page.get('retrieval_status') or '不明'}。"
            item["resolution_method"] = "automated_screening_v1"
            item["resolution_evidence"] = evidence
            resolved.append(item["pre_id"])
            log.append({"pre_id": item.get("pre_id"), "url": item.get("url"), **evidence, "decision": decision})
        time.sleep(fetcher.PAUSE_SECONDS)

    if not resolved:
        print(f"[Auto screen] No high-confidence exclusions. {len(open_items)} items remain open.")
        return 0

    LEDGER_PATH.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    previous = []
    if LOG_PATH.exists():
        try:
            payload = json.loads(LOG_PATH.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                previous = payload
        except json.JSONDecodeError:
            print("[Auto screen] Existing log is invalid JSON; refusing to overwrite it.", file=sys.stderr)
            return 2
    LOG_PATH.write_text(json.dumps(previous + log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[Auto screen] Resolved: {len(resolved)} / {len(open_items)} open items")
    print("[Auto screen] Resolved PRE IDs: " + ", ".join(resolved))
    print("[Auto screen] Ambiguous, blocked, and temporary failures remain open.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
