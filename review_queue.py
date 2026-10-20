import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from common import now_jst, get_period


REVIEW_DIR = Path("data/review")
REVIEW_FILE = REVIEW_DIR / "classification_review.json"

# Explicitly removed/deleted-page messages. Do not treat 403/429/timeouts as dead links.
REMOVED_PAGE_PATTERNS = (
    r"this topic does not exist",
    r"the requested topic does not exist",
    r"this page (?:has been|was) removed",
    r"this content is no longer available",
    r"投稿が削除されました",
    r"ページが見つかりません",
    r"記事が存在しません",
)

# Strong request-only language. These phrases are only sufficient when the page
# contains no plausible downloadable asset, attachment, resource link, or code.
REQUEST_ONLY_PATTERNS = (
    r"\blooking for\b",
    r"\bcan anyone (?:make|share|provide|give|draw|create|upload)\b",
    r"\bcan someone (?:make|share|provide|give|draw|create|upload)\b",
    r"\bdoes anyone have\b",
    r"\banyone (?:got|have|willing to share)\b",
    r"\bgimme\b",
    r"\bplease make\b",
    r"\bneed help finding\b",
    r"\brequest(?:ing)? (?:a|an|some|for)\b",
    r"\bhelp me find\b",
    r"\bcerco\b",
    r"\brichiesta\b",
    r"\bqualcuno (?:ha|può|potrebbe)\b",
    r"\bmi serve\b",
    r"ищу",
    r"помогите найти",
    r"запрос на",
    r"素材を探しています",
    r"素材を探している",
    r"素材募集",
    r"素材をください",
    r"素材ください",
    r"素材を作って",
    r"配布してほしい",
    r"くれくれ",
    r"作ってください",
    # Discussion/question-only posts are excluded only when no resource evidence exists.
    r"\bdiscussion\b",
    r"\bwhat do you think\b",
    r"\bany thoughts\b",
    r"\bfeedback (?:please|wanted|needed)\b",
    r"\bquestion about\b",
    r"\bhow do i\b",
    r"\bdiscussione\b",
    r"\bopinioni\b",
    r"обсуждение",
    r"вопрос о",
    r"意見を聞かせて",
    r"質問です",
    r"相談です",
)

RESOURCE_LINK_PATTERN = re.compile(
    r"(download|attachment|\.zip(?:$|[?#])|\.rar(?:$|[?#])|\.7z(?:$|[?#])|"
    r"\.js(?:$|[?#])|\.rb(?:$|[?#])|\.ogg(?:$|[?#])|\.mp3(?:$|[?#])|"
    r"\.wav(?:$|[?#])|\.png(?:$|[?#])|\.jpg(?:$|[?#])|\.webp(?:$|[?#])|"
    r"mediafire|mega\.nz|drive\.google|dropbox|itch\.io|opengameart|"
    r"ダウンロード|配布|素材|scarica|скачать)",
    re.IGNORECASE,
)



def _content_nodes(soup):
    """Return likely post-content blocks, avoiding most forum navigation chrome."""
    selectors = (
        ".ipsComment_content",
        ".cPost_contentWrap",
        ".postarea",
        ".post_body",
        ".post-body",
        ".messageContent",
        ".message-content",
        ".post-content",
        "article",
    )
    for selector in selectors:
        nodes = soup.select(selector)
        if nodes:
            return nodes
    return [soup.body or soup]


def _page_has_resource_evidence(nodes):
    for node in nodes:
        if node.select_one("pre, code, .attachment, .file, .download, a[download]"):
            code = " ".join(part.get_text(" ", strip=True) for part in node.select("pre, code"))
            if len(code) >= 180 or node.select_one(".attachment, .file, .download, a[download]"):
                return True
        for anchor in node.select("a[href]"):
            href = str(anchor.get("href") or "")
            label = anchor.get_text(" ", strip=True)
            if RESOURCE_LINK_PATTERN.search(href) or RESOURCE_LINK_PATTERN.search(label):
                return True
        for image in node.select("img[src]"):
            src = str(image.get("src") or "")
            alt = str(image.get("alt") or "")
            # Ignore typical avatars and interface icons; retain likely shared artwork.
            if not re.search(r"(avatar|profile|emoji|smil|icon|logo)", src + " " + alt, re.I):
                return True
    return False


def audit_open_review_items(queue, max_items=30):
    """
    Conservatively pre-screen open review entries.

    Automatically resolves only:
    - a target page returning HTTP 404/410;
    - a page clearly displaying a removed/nonexistent-page message;
    - an explicit resource request with no plausible asset/download/code evidence.

    Access-denied, rate-limit, network, and ambiguous results remain open.
    A bounded batch prevents a single scheduled run from hammering old forums.
    """
    items = queue.get("items", [])
    now = now_jst()
    checked = 0
    resolved = []
    skipped_recent = 0

    for item in items:
        if item.get("status") != "open" or not item.get("url"):
            continue

        audit = item.get("link_audit") or {}
        checked_at = audit.get("checked_at")
        if checked_at:
            try:
                from datetime import datetime, timedelta
                previous = datetime.fromisoformat(checked_at)
                prior_result = audit.get("result")
                # Retry access/network failures sooner; successful or conclusive
                # checks need not be repeated every day.
                retry_days = 1 if prior_result in (
                    "network_error_not_proven_dead",
                    "inaccessible_not_proven_dead",
                    "uncertain",
                ) else 14
                if now - previous < timedelta(days=retry_days):
                    skipped_recent += 1
                    continue
            except (TypeError, ValueError):
                pass

        if checked >= max_items:
            break

        url = str(item["url"]).strip()
        if not url.startswith(("http://", "https://")):
            continue

        checked += 1
        audit_result = {
            "checked_at": now.isoformat(timespec="seconds"),
            "status_code": None,
            "final_url": url,
            "result": "uncertain",
            "reason": None,
        }

        try:
            response = requests.get(
                url,
                timeout=6,
                allow_redirects=True,
                headers={"User-Agent": "RPGMakerDailyReport/1.0 (resource-link audit)"},
            )
            audit_result["status_code"] = response.status_code
            audit_result["final_url"] = response.url

            if response.status_code in (404, 410):
                audit_result.update(result="dead_page", reason=f"HTTP {response.status_code}")
            elif response.status_code >= 400:
                audit_result.update(result="inaccessible_not_proven_dead", reason=f"HTTP {response.status_code}; retained")
            elif "text/html" in response.headers.get("Content-Type", "").lower():
                soup = BeautifulSoup(response.text, "html.parser")
                nodes = _content_nodes(soup)
                content_text = " ".join(node.get_text(" ", strip=True) for node in nodes)
                content_lower = content_text.lower()

                removed_match = next(
                    (pattern for pattern in REMOVED_PAGE_PATTERNS if re.search(pattern, content_lower, re.I)),
                    None,
                )
                if removed_match:
                    audit_result.update(result="dead_page", reason=f"Removed-page marker: {removed_match}")
                else:
                    title = str(item.get("title") or "")
                    request_text = (title + " " + content_text[:6000]).lower()
                    request_match = next(
                        (pattern for pattern in REQUEST_ONLY_PATTERNS if re.search(pattern, request_text, re.I)),
                        None,
                    )
                    if request_match and not _page_has_resource_evidence(nodes):
                        audit_result.update(
                            result="request_without_resource",
                            reason=f"Explicit request language with no detected asset/download/code: {request_match}",
                        )
                    else:
                        audit_result.update(result="page_accessible", reason="No conclusive exclusion evidence")
            else:
                audit_result.update(result="page_accessible", reason="Page responded successfully; content type not HTML")
        except requests.RequestException as exc:
            audit_result.update(
                result="network_error_not_proven_dead",
                reason=f"{type(exc).__name__}; retained",
            )

        item["link_audit"] = audit_result

        if audit_result["result"] in ("dead_page", "request_without_resource"):
            item["status"] = "resolved"
            item["decision"] = "not_applicable"
            item["resolved_at"] = now.isoformat(timespec="seconds")
            if audit_result["result"] == "dead_page":
                item["review_note"] = f"自動事前確認：配布元ページを確認できず（{audit_result['reason']}）。素材確認キューから除外。"
            else:
                item["review_note"] = f"自動事前確認：質問・議論・素材募集などの投稿で、ページ内に配布物を確認できず（{audit_result['reason']}）。素材確認キューから除外。"
            resolved.append(item.get("pre_id"))

    return {
        "checked": checked,
        "resolved": len(resolved),
        "resolved_pre_ids": resolved,
        "skipped_recent": skipped_recent,
    }

def load_review_queue():
    """
    分類確認キューを読み込む。

    ファイルが存在しない場合は空のキューを返す。
    """
    if not REVIEW_FILE.exists():
        return {
            "version": 1,
            "next_pre_number": 1,
            "items": [],
        }

    try:
        with REVIEW_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {
            "version": 1,
            "next_pre_number": 1,
            "items": [],
        }

    if not isinstance(data, dict):
        return {
            "version": 1,
            "next_pre_number": 1,
            "items": [],
        }

    data.setdefault("version", 1)
    data.setdefault("next_pre_number", 1)
    data.setdefault("items", [])

    return data


def save_review_queue(queue):
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)

    with REVIEW_FILE.open("w", encoding="utf-8") as f:
        json.dump(
            queue,
            f,
            indent=2,
            ensure_ascii=False,
        )


def _next_pre_id(queue):
    number = int(queue.get("next_pre_number", 1))
    queue["next_pre_number"] = number + 1
    return f"PRE-{number:05d}"


def _find_by_internal_id(queue, internal_id):
    for entry in queue.get("items", []):
        if entry.get("internal_id") == internal_id:
            return entry
    return None


def prepare_classification_reviews(items, queue):
    """
    needs_review のItemを確認キューへ登録する。

    既に確認済みのItemは再登録しない。
    新規レビュー対象にはPRE-xxxxxを付与する。
    """
    review_items = []

    for item in items:
        resource_intent = item.get("resource_intent")

        # New hierarchical triage:
        # - clear non-resources do not enter the resource classification queue;
        # - clear resource candidates continue with automatic detailed taxonomy;
        # - all uncertain items enter human review; missing evidence is not
        #   proof that an item is not a resource.
        # Historical items without resource_intent keep the previous behavior.
        if resource_intent == "not_resource":
            continue

        if resource_intent == "resource_candidate":
            continue

        if resource_intent != "uncertain" and item.get("classification_status") != "needs_review":
            continue

        internal_id = item.get("internal_id")
        if not internal_id:
            continue

        existing = _find_by_internal_id(queue, internal_id)

        if existing:
            if existing.get("status") == "open":
                item["pre_id"] = existing.get("pre_id")
                review_items.append(item)
            continue

        pre_id = _next_pre_id(queue)
        item["pre_id"] = pre_id

        queue["items"].append({
            "pre_id": pre_id,
            "internal_id": internal_id,
            "source_site_id": item.get("source_site_id"),
            "source": item.get("source"),
            "collector": item.get("collector"),
            "url": item.get("url"),
            "title": item.get("title"),
            # 次回以降の判断根拠を残し、URLだけを見直す作業を減らす。
            "description": str(item.get("description") or item.get("body_text") or item.get("body") or "")[:1600],
            "source_tags": item.get("source_tags", [])[:30] if isinstance(item.get("source_tags"), list) else [],
            "tags": item.get("tags", [])[:30] if isinstance(item.get("tags"), list) else [],
            "category": item.get("category"),
            "asset_type": item.get("asset_type"),
            "content_type": item.get("content_type"),
            "classification_confidence": item.get(
                "classification_confidence"
            ),
            "classification_status": "needs_review",
            "classification_margin": item.get(
                "classification_margin"
            ),
            "classification_scores": item.get(
                "classification_scores",
                {},
            ),
            "classification_evidence": item.get(
                "classification_evidence",
                [],
            ),
            "created_at": now_jst().isoformat(),
            "created_report_date": now_jst().strftime("%Y-%m-%d"),
            "created_report_period": get_period(),
            "status": "open",
            "decision": None,
            "resolved_at": None,
            "review_note": None,
        })

        review_items.append(item)

    return review_items


def get_open_review_items(queue):
    """
    現在未解決の分類確認Itemを返す。
    """
    return [
        item
        for item in queue.get("items", [])
        if item.get("status") == "open"
    ]


def get_carryover_review_items(queue, current_review_items):
    """
    今回のレポートで新たに確認対象となったItemを除き、
    前回までから持ち越されている未解決Itemを返す。
    """
    current_pre_ids = {
        item.get("pre_id")
        for item in current_review_items
        if item.get("pre_id")
    }

    return [
        item
        for item in queue.get("items", [])
        if item.get("status") == "open"
        and item.get("pre_id") not in current_pre_ids
    ]
