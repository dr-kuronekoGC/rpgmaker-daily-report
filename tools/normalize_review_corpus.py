#!/usr/bin/env python3
"""Normalize human review notes into an auditable, non-authoritative corpus.

This tool deliberately does not use the ledger's decision field as a binary
include/exclude target. Its output is an audit aid only; it does not change
collection, classification, or Slack reporting behavior.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

LEDGER_PATH = Path("data/review/classification_review.json")

PAID_RE = re.compile(r"有料|販売|販売の案内|販売のお知らせ|paid|price|\$\s?\d", re.I)
TEMP_PROMO_RE = re.compile(r"タイムセール|時間限定|期間限定|タイムセール|割引|セール|抽選プレゼント|プレゼント|giveaway", re.I)
UNAVAILABLE_RE = re.compile(r"削除|取得できなかった|判定不能|本文を確認できない|unavailable|deleted", re.I)
DUPLICATE_RE = re.compile(r"重複|既出|リマインド|同じ内容|統合|duplicate", re.I)
PERSONAL_RE = re.compile(r"個人的な好み|個人的な判断|編集方針|ユーザー判断|ユーザー確認", re.I)
COPYRIGHT_RE = re.compile(r"著作権|版権|copyright|dragon ball|lego", re.I)
DISCUSSION_RE = re.compile(r"質問|相談|雑談|議論|話題・議論|情報共有", re.I)
SHOWCASE_RE = re.compile(r"自作ゲーム|ゲームの紹介|自作ゲームの紹介|自作ゲームの画面|スクリーンショット|制作過程|進捗紹介|制作状況|playthru|showcase", re.I)
PREVIEW_RE = re.compile(r"サンプル表示|サンプル画面|サンプル|プレビュー|素材そのものではない", re.I)
OFFICIAL_RE = re.compile(r"公式情報|公式.*更新|official", re.I)
TOOL_RE = re.compile(r"制作支援ツール|ツールとして採用|dev tools|save files|save-file|logic builder|tool", re.I)
DELIVERABLE_RE = re.compile(r"素材|プラグイン|タイルセット|キャラクターセット|音素材|効果音|キャラクター素材|キャラセット|有料|無料プラグイン", re.I)


def normalize(item: dict[str, Any]) -> dict[str, Any]:
    title = str(item.get("title") or "")
    note = str(item.get("review_note") or "")
    text = f"{title}\n{note}"
    decision = item.get("decision")
    purpose: list[str] = []
    flags: list[str] = []
    recommendation = "needs_review"
    rationale = "レビュー記録だけでは一般化できる採否ルールを確定できない。"

    if UNAVAILABLE_RE.search(text):
        purpose.append("unavailable")
        recommendation = "exclude_unavailable"
        rationale = "削除・取得不能など、内容を確認できない記録。素材ではないと断定せず、利用不可として扱う。"
        flags.append("content_unavailable")
    elif DUPLICATE_RE.search(text):
        purpose.append("duplicate_or_reminder")
        recommendation = "exclude_duplicate"
        rationale = "既出・重複と明記された記録。参照先の既存項目へ統合する。"
        flags.append("duplicate_check")
    elif COPYRIGHT_RE.search(text):
        purpose.append("copyright_or_fanwork_concern")
        recommendation = "manual_review_exception"
        rationale = "権利上の懸念が記録されている。キーワードだけで一般化せず、個別確認する。"
        flags.append("rights_review")
    elif re.search(r"Source Check|分類確認キューから除外|詳細分類の対象外", text, re.I):
        purpose.append("source_check_or_out_of_scope")
        recommendation = "exclude_out_of_scope"
        rationale = "詳細な素材分類の対象外として記録されている。"
    elif DISCUSSION_RE.search(text) and not re.search(r"素材.*採用|プラグイン.*採用|素材.*公開対象|素材.*配布", note):
        purpose.append("question_discussion_or_chat")
        recommendation = "exclude_discussion"
        rationale = "質問・相談・雑談が中心で、再利用可能な成果物の配布情報とは記録されていない。"
    elif SHOWCASE_RE.search(text) and not re.search(r"素材.*採用|素材.*公開対象|素材.*配布|プラグイン.*採用|制作支援ツール", note):
        purpose.append("game_showcase_or_process")
        recommendation = "exclude_showcase"
        rationale = "ゲーム紹介・画面・制作過程が中心で、汎用的な配布物の記録がない。"
    elif PREVIEW_RE.search(note) and not re.search(r"主として素材|素材として採用|素材.*公開対象|素材配布|素材へのリンク", note):
        purpose.append("sample_or_preview_without_deliverable")
        recommendation = "exclude_preview"
        rationale = "サンプル・プレビューのみと記録され、実際の配布物が確認されていない。"
    elif OFFICIAL_RE.search(text):
        purpose.append("official_or_product_update")
        recommendation = "include_candidate" if decision == "confirmed" else "needs_review"
        rationale = "公式・製品更新情報の候補。具体的な更新内容と継続的な有用性を確認する。"
    elif PAID_RE.search(text) and decision == "not_applicable":
        purpose.append("paid_product_or_store_listing")
        recommendation = "reassess_paid_policy"
        rationale = "過去は除外されたが、現在の方針では有料であること自体は除外理由にならない。恒久的な商品情報か、一時的な販促だけかを再評価する。"
        flags.append("paid_policy_changed")
    elif TEMP_PROMO_RE.search(text):
        purpose.append("temporary_promotion_or_giveaway")
        recommendation = "reassess_promotion"
        rationale = "期間限定の割引・配布企画の可能性がある。具体的な商品情報が残るなら商品を候補にし、販促だけなら除外する。"
        flags.append("promotion_persistence_check")
    elif TOOL_RE.search(text):
        purpose.append("developer_tool")
        recommendation = "include_candidate" if decision == "confirmed" else "needs_review"
        rationale = "汎用的な制作支援ツールの候補。無料・有料ではなく、利用可能なツールの実体を確認する。"
    elif DELIVERABLE_RE.search(text):
        purpose.append("asset_plugin_or_product")
        recommendation = "include_candidate" if decision == "confirmed" else "needs_review"
        rationale = "素材・プラグイン・商品情報の候補。既存の詳細分類と実際の配布・販売先を確認する。"
    else:
        purpose.append("unclear_or_other")
        recommendation = "needs_review"

    if PERSONAL_RE.search(note):
        flags.append("individual_editorial_exception")
    if item.get("status") == "open":
        flags.append("still_open")
        if recommendation not in {"exclude_unavailable", "exclude_duplicate", "exclude_out_of_scope"}:
            recommendation = "needs_review"

    return {
        "pre_id": item.get("pre_id"),
        "title": title,
        "source": item.get("source"),
        "url": item.get("url"),
        "status": item.get("status"),
        "historical_decision": decision,
        "review_note": note,
        "purpose_labels": purpose,
        "audit_recommendation": recommendation,
        "flags": sorted(set(flags)),
        "rationale": rationale,
    }


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else LEDGER_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[Normalize] Cannot read {path}: {exc}", file=sys.stderr)
        return 2

    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        print(f"[Normalize] Expected an object with an items list in {path}", file=sys.stderr)
        return 2

    normalized = [normalize(item) for item in items if isinstance(item, dict)]
    counts: dict[str, int] = {}
    for item in normalized:
        key = item["audit_recommendation"]
        counts[key] = counts.get(key, 0) + 1

    output = {
        "schema_version": 1,
        "source_ledger": str(path),
        "item_count": len(normalized),
        "note": "Audit aid only. Does not alter runtime behavior. Historical decision is retained but is not treated as a binary label.",
        "recommendation_counts": dict(sorted(counts.items())),
        "items": normalized,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
