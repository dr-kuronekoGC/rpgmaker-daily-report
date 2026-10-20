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
AUDIT_PATH = Path("data/review/auto_screen_audit.json")
JST = timezone(timedelta(hours=9))

# Avoid long hangs on sites that are currently blocking or timing out.
fetcher.TIMEOUT = 8
fetcher.PAUSE_SECONDS = 0.15

RESOLVED_MARKER_RE = re.compile(r"\b(?:solved|resolved|filled|answered|completed)\b", re.I)
REQUEST_RE = re.compile(
    r"\b(?:looking for|searching for|request(?:ing)?|need(?:ing)?|"
    r"can anyone (?:make|share|provide|create)|anyone have|gimme|give me|"
    r"need help finding|does anyone have|wanted|request for images|image request|"
    r"resource request|sound request|plugin request|please make|could you make|"
    r"can you make|suche|gesucht|kann mir jemand|hat jemand|bitte um|"
    r"cerco|cercasi|richiesta|mi serve|je cherche|recherche|besoin de|aidez-moi)\b"
    r"|(?:ищу|ищем|помогите найти|нужен|нужна|нужны|где найти|素材を探しています|"
    r"素材を探している|素材募集|素材をください|画像をください|画像ください|"
    r"素材ください|作ってください|探しています|探してます|求む|くれくれ)",
    re.I,
)

BODY_REQUEST_RE = re.compile(
    r"\b(?:looking for|searching for|request(?:ing)?\s+(?:a|an|some|for)|"
    r"need help finding|can anyone (?:make|share|provide|create)|"
    r"anyone have|does anyone have|help me find|where can i find|"
    r"i am looking for|i'm looking for|seeking (?:a|an|some)|"
    r"can someone (?:make|share|provide|create)|"
    r"could someone (?:make|share|provide|create)|"
    r"je cherche|cerco|cercasi|ищу|ищем|помогите найти|где найти)\b"
    r"|(?:素材を探しています|素材を探している|素材募集|素材をください|"
    r"画像をください|画像ください|素材ください|求む|くれくれ)",
    re.I,
)
DISCUSSION_RE = re.compile(
    r"\b(?:discussion|discuss|what do you think|which is better|"
    r"how do i|how can i|why does|is there a way|question|help with|"
    r"discussione|opinioni|diskussion|meinung|обсуждение|вопрос)\b"
    r"|(?:質問|相談|意見を聞かせて)",
    re.I,
)
SHOWCASE_RE = re.compile(
    r"\b(?:showcase|my game|my project|my works|work in progress|\bwip\b|"
    r"development process|making of|screenshots?|gameplay video|mapping showcase|"
    r"miei lavori|le mie creazioni|il mio progetto|mon projet|mes créations|"
    r"mein projekt|meine arbeiten|мои работы|мой проект|мой арт)\b"
    r"|(?:作品紹介|制作過程|スクリーンショット|ゲームプレイ動画)",
    re.I,
)
NO_DELIVERABLE_RE = re.compile(
    r"\b(?:not a resource|no download|not available for download|"
    r"not for download|just (?:a )?(?:screenshot|preview|showcase)|"
    r"only a preview|not sharing (?:this|these|it)|not a release|"
    r"no files? (?:attached|provided)|made only for my own game|"
    r"no download link|no files provided|not releasing|only screenshots|"
    r"just showing my game|не для скачивания|без скачивания)\b"
    r"|(?:素材配布ではない|配布していません|ダウンロード不可|プレビューのみ|"
    r"スクリーンショットのみ|自分のゲーム専用)",
    re.I,
)
POSITIVE_RELEASE_RE = re.compile(
    r"\b(?:downloadable|download link|download here|release page|"
    r"release available|resource pack|asset pack|sound pack|audio pack|"
    r"pack of sounds|sound archive|archive of sounds|free to use|"
    r"available for use|get it here|mediafire|mega\.nz|dropbox|"
    r"google drive|yadi\.sk|disk\.yandex|yandex\.(?:ru|com)|ya\.ru|"
    r"itch\.io|github\.com|\.zip\b|\.rar\b|\.7z\b|"
    r"\.ogg\b|\.mp3\b|\.wav\b|\.js\b|архив звуков|пак звуков|"
    r"звуковой архив|пак со звуками|ссылка на папку|скачать)",
    re.I,
)
ASSET_WORD_RE = re.compile(
    r"\b(?:sprite|sprites|charset|battler|tileset|tile set|icon pack|"
    r"resource|asset|plugin|script|bgm|bgs|sound effect|music pack|"
    r"animation sheet|sound pack|tool)\b",
    re.I,
)
RESOURCE_LINK_RE = re.compile(
    # Link URLs and anchor labels use different languages across the forums.
    # Include common download/archive/resource terms so old posts with generic
    # file-hosting URLs are not silently skipped by the link audit.
    r"download|descargar|t[eé]l[eé]charger|herunterladen|scarica|scaricare|"
    r"скачать|загрузить|скачиван|downloaden|"
    r"mediafire|mega\.nz|dropbox|drive\.google|google drive|"
    r"yadi\.sk|disk\.yandex|yandex\.(?:ru|com)|ya\.ru|"
    r"\.zip(?:$|[?#])|\.rar(?:$|[?#])|\.7z(?:$|[?#])|"
    r"\.ogg(?:$|[?#])|\.mp3(?:$|[?#])|\.wav(?:$|[?#])|"
    r"\.png(?:$|[?#])|\.jpe?g(?:$|[?#])|\.gif(?:$|[?#])|"
    r"\.js(?:$|[?#])|/downloads?(?:/|$)|/art/|itch\.io|"
    r"github\.com/.*/releases|"
    r"архив|файл|файлы|музык|звуков|ресурс|плагин|спрайт|тайлсет|"
    r"анимац|иконк|материал|скачив|"
    r"download[- ]?link|freebie|asset pack|resource pack|sound pack|"
    r"scaricamento|download gratuit|t[eé]l[eé]chargement|"
    r"herunterladen|datei|ressourcen|materialien|"
    r"descarga|archivo|recursos|"
    r"ダウンロード|配布|素材|添付|ファイル|音源|効果音|BGM|プラグイン",
    re.I,
)
# Check every detected resource link (the page parser caps extracted links at 100).
# This avoids keeping a resource when only the first three of many download links were checked.
MAX_RESOURCE_LINKS = 100
LINK_TIMEOUT = 3

# The user consistently excludes posts whose purpose is only to advertise a
# discount, time-limited sale, coupon, or contest giveaway. A product/store
# URL alone is not evidence that a usable downloadable file is included.
PROMOTION_ONLY_RE = re.compile(
    r"\b(?:limited[- ]time (?:sale|offer|discount|deal)|flash sale|"
    r"time[- ]limited (?:offer|discount|sale)|discount(?:ed)?|coupon|"
    r"promo code|sale ends|on sale|price drop|special offer|"
    r"giveaway contest|enter to win|raffle|"
    r"limited offer|discount code|free for a limited time)\b"
    r"|(?:期間限定(?:セール|割引|販売|配布)|タイムセール|割引クーポン|"
    r"セール終了|抽選プレゼント|抽選でプレゼント|期間限定の割引|"
    r"скидк|распродаж|розыгрыш|только сегодня|"
    r"offerta a tempo limitato|sconto|codice sconto|"
    r"vente flash|offre limitée|réduction|code promo|"
    r"zeitlich begrenz(?:t|te) (?:Angebot|Rabatt)|Rabattcode)",
    re.I,
)
DIRECT_DOWNLOAD_RE = re.compile(
    r"download|descargar|t[eé]l[eé]charger|herunterladen|scarica|scaricare|"
    r"скачать|загрузить|mediafire|mega\.nz|dropbox|drive\.google|"
    r"google drive|yadi\.sk|disk\.yandex|yandex\.(?:ru|com)|ya\.ru|"
    r"\.(?:zip|rar|7z|ogg|mp3|wav|js)(?:$|[?#])|/downloads?(?:/|$)|"
    r"ダウンロード|添付ファイル|ファイルをダウンロード",
    re.I,
)


def has_direct_download_link(link_check: dict) -> bool:
    for result in link_check.get("results") or []:
        if DIRECT_DOWNLOAD_RE.search(clean(result.get("url"))) or DIRECT_DOWNLOAD_RE.search(clean(result.get("text"))):
            return True
    return False


def check_resource_links(session, page: dict, source_url: str) -> dict:
    """Check obvious resource links only; ambiguous results never exclude."""
    candidates = []
    seen = set()
    for link in page.get("outbound_links") or []:
        if not isinstance(link, dict):
            continue
        target = clean(link.get("url"))
        label = clean(link.get("text"))
        if not target.startswith(("http://", "https://")) or target in seen:
            continue
        if not RESOURCE_LINK_RE.search(target) and not RESOURCE_LINK_RE.search(label):
            continue
        seen.add(target)
        candidates.append({"text": label[:160], "url": target})
    if not candidates:
        return {"candidate_count": 0, "checked_count": 0, "all_checked_dead": False, "results": []}

    checked = []
    for candidate in candidates[:MAX_RESOURCE_LINKS]:
        status = None
        method = "HEAD"
        error = None
        try:
            response = session.head(
                candidate["url"], allow_redirects=True, timeout=LINK_TIMEOUT,
                headers={"User-Agent": fetcher.USER_AGENT},
            )
            status = response.status_code
            response.close()
            if status in {403, 405, 501}:
                method = "GET"
                response = session.get(
                    candidate["url"], allow_redirects=True, timeout=LINK_TIMEOUT,
                    headers={"User-Agent": fetcher.USER_AGENT}, stream=True,
                )
                status = response.status_code
                response.close()
        except fetcher.requests.RequestException as exc:
            error = type(exc).__name__
        checked.append({
            **candidate,
            "http_status": status,
            "method": method,
            "error": error,
            "dead": status in {404, 410},
            "reachable": status is not None and 200 <= status < 400,
        })

    all_dead = (
        len(candidates) <= MAX_RESOURCE_LINKS
        and len(checked) == len(candidates)
        and bool(checked)
        and all(result["dead"] for result in checked)
    )
    return {
        "candidate_count": len(candidates),
        "checked_count": len(checked),
        "all_checked_dead": all_dead,
        "results": checked,
    }


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
    link_check = page.get("resource_link_check") or {}

    # Preserve explicit human corrections before applying any automatic rule,
    # including link-death rules. Human review takes precedence over heuristics.
    human_reopen_note = clean(item.get("review_note"))
    if re.search(
        r"(?:自動判定を取り消し|自動除外を取り消し|除外判定を取り消し|未確認に戻す|再確認対象として残す)",
        human_reopen_note,
    ):
        return None

    if status in {404, 410}:
        return ("not_applicable", f"保存されたURLがHTTP {status}を返し、現在ページを取得できない")
    if is_direct_profile(url):
        return ("not_applicable", "個別の素材・配布物ではなく、ユーザープロフィールへの直リンク")
    if link_check.get("all_checked_dead"):
        return ("not_applicable", "投稿内で特定できたダウンロード／素材リンクがすべてHTTP 404/410で、配布先を確認できない")

    if retrieval != "body_found" or not body:
        # A blank/blocked response is not evidence of absence.
        return None

    positive_release = bool(POSITIVE_RELEASE_RE.search(combined))
    resolved_marker = bool(RESOLVED_MARKER_RE.search(title))
    copyright_warning = bool(COPYRIGHT_WARNING_RE.search(combined))

    # Exclude only explicit promotion/discount/contest announcements when the
    # post has no direct downloadable destination. Ordinary paid assets and
    # external storefront links are not excluded by themselves.
    promotion_context = f"{title}\n{body[:1800]}"
    if PROMOTION_ONLY_RE.search(promotion_context) and not has_direct_download_link(link_check):
        return (
            "not_applicable",
            "過去の確認方針に基づき、割引・期間限定セール・抽選告知が主目的で、直接取得できる素材ファイルへのリンクを確認できないため除外",
        )

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
    # Broad words such as "need" or "gimme" are safe in a title, but in
    # a thread body they often appear in offers/replies on genuine resource
    # posts (e.g. "if you need a piece, send me the sheet music"). Require
    # explicit seeking/request phrasing in body text to avoid false exclusions.
    request_signal = bool(REQUEST_RE.search(title) or BODY_REQUEST_RE.search(body[:1800]))
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
    audit_rows = []

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
        page["resource_link_check"] = check_resource_links(session, page, clean(item.get("url")))
        outcome = classify_page(item, page)
        audit_rows.append({
            "pre_id": item.get("pre_id"),
            "source": item.get("source"),
            "title": clean(item.get("title"))[:300],
            "url": clean(item.get("url")),
            "http_status": page.get("http_status"),
            "retrieval_status": page.get("retrieval_status"),
            "retrieval_method": page.get("retrieval_method"),
            "resource_link_check": page.get("resource_link_check"),
            "suggestion": outcome[0] if outcome else "keep_open",
            "reason": outcome[1] if outcome else "",
        })
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
                "resource_link_check": page.get("resource_link_check"),
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

    audit_payload = {
        "schema_version": 1,
        "checked_at": now,
        "scanned_item_count": len(audit_rows),
        "auto_resolved_count": len(resolved),
        "note": "Latest pass over items that were open at scan start. HTTP 403/429/5xx, timeouts, and ambiguous resource links are not treated as dead links.",
        "items": audit_rows,
    }
    AUDIT_PATH.write_text(json.dumps(audit_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not resolved:
        print(f"[Auto screen] No high-confidence exclusions. {len(open_items)} items remain open.")
        print(f"[Auto screen] Wrote link/retrieval audit for {len(audit_rows)} items.")
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
