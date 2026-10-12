import json
from pathlib import Path

from common import now_jst, get_period


REVIEW_DIR = Path("data/review")
REVIEW_FILE = REVIEW_DIR / "classification_review.json"


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
