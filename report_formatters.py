import os
import re
import requests

from common import (
    now_jst,
    get_period,
)

from config import (
    REQUEST_TIMEOUT,
    SLACK_WEBHOOK_ENV,
    SOURCE_CHECK_SITES,
    OFFICIAL_INFORMATION_LINKS,
)

from categories import DISPLAY_CATEGORY
from language import detect_language


# ==========================================
# Category Display
# ==========================================

CATEGORY_GROUPS = {
    "★★★★★ 今日の注目": [
        "本体ニュース",
        "UNITE",
        "Forum重要事項",
    ],

    "★★★★☆ 新作ゲーム": [
        "ゲーム",
    ],

    "★★★☆☆ プラグイン・素材": [
        "プラグイン",
        "素材",
    ],

    "★★☆☆☆ 開発情報・Tips": [
        "Tips",
    ],

    "★☆☆☆☆ 質問・相談": [
        "質問",
    ],
}


DISPLAY_ORDER = [
    "本体ニュース",
    "UNITE",
    "Forum重要事項",
    "プラグイン",
    "素材",
    "ゲーム",
    "Tips",
    "質問",
]


# ==========================================
# Category Helpers
# ==========================================

def get_display_category(category):

    """
    内部カテゴリをSlack表示用カテゴリへ変換する。
    """

    info = DISPLAY_CATEGORY.get(
        category
    )

    if isinstance(info, dict):

        group = info.get(
            "group"
        )

        if group == "グラフィック素材":
            return "グラフィック素材"

        if group == "サウンド素材":
            return "サウンド素材"

        if group == "プラグイン":
            return "プラグイン"

        if group == "ゲーム":
            return "ゲーム"

        if group == "Tips":
            return "Tips"

        if group == "質問":
            return "質問"

        if group == "公式":
            return category

    return category


def get_report_group(category):

    """
    サマリー表示用の大分類を返す。
    """

    display_category = get_display_category(
        category
    )

    if display_category in (
        "プラグイン",
        "グラフィック素材",
        "サウンド素材",
    ):
        return "プラグイン・素材"

    if display_category == "ゲーム":
        return "新作ゲーム"

    if display_category == "Tips":
        return "開発情報・Tips"

    if display_category == "質問":
        return "質問・相談"

    if display_category in (
        "本体ニュース",
        "UNITE",
        "Forum重要事項",
    ):
        return "今日の注目"

    if display_category == "SourceCheck":
        return "Source Check"

    return None


# ==========================================
# DeviantArt Detail
# ==========================================

def format_deviantart_detail(
    item,
):
    """
    DeviantArtから取得した詳細情報を
    Slack表示用テキストに変換する。

    取得できない情報は表示しない。

    license はAPIから返された値を
    そのまま表示する。
    """

    lines = []

    # --------------------------------------
    # Author
    # --------------------------------------

    author = item.get(
        "author"
    )

    if isinstance(
        author,
        str,
    ) and author.strip():

        lines.append(
            f"  作者：{author.strip()}"
        )

    # --------------------------------------
    # Tags
    # --------------------------------------

    source_tags = item.get(
        "source_tags"
    )

    if isinstance(
        source_tags,
        list,
    ):

        clean_tags = []

        for tag in source_tags:

            if not isinstance(
                tag,
                str,
            ):
                continue

            tag = tag.strip()

            if not tag:
                continue

            if tag not in clean_tags:
                clean_tags.append(
                    tag
                )

        if clean_tags:

            # Slackが長くなりすぎないように
            # 最大20タグまで表示。
            display_tags = clean_tags[:20]

            tag_text = ", ".join(
                display_tags
            )

            if len(clean_tags) > 20:
                tag_text += " ..."

            lines.append(
                f"  タグ：{tag_text}"
            )

    # --------------------------------------
    # License
    # --------------------------------------

    license_name = item.get(
        "license"
    )

    if isinstance(
        license_name,
        str,
    ) and license_name.strip():

        lines.append(
            "  ライセンス："
            f"{license_name.strip()}"
        )

    # --------------------------------------
    # Download
    # --------------------------------------

    is_downloadable = item.get(
        "is_downloadable"
    )

    if isinstance(
        is_downloadable,
        bool,
    ):

        if is_downloadable:

            lines.append(
                "  ダウンロード：可能"
            )

        else:

            lines.append(
                "  ダウンロード：不可"
            )

    # --------------------------------------
    # Mature
    # --------------------------------------

    is_mature = item.get(
        "is_mature"
    )

    if is_mature is True:

        lines.append(
            "  Mature：あり"
        )

    # --------------------------------------
    # Description
    # --------------------------------------

    description = item.get(
        "description"
    )

    if isinstance(
        description,
        str,
    ):

        description = description.strip()

        if description:

            # 改行をSlack上で扱いやすくする。
            description = (
                description
                .replace("\r\n", " ")
                .replace("\n", " ")
                .replace("\r", " ")
            )

            # 連続空白を整理。
            while "  " in description:
                description = (
                    description.replace(
                        "  ",
                        " ",
                    )
                )

            # 長すぎる説明は切る。
            max_length = 300

            if len(description) > max_length:

                description = (
                    description[
                        :max_length
                    ].rstrip()
                    + "..."
                )

            lines.append(
                f"  説明：{description}"
            )

    # --------------------------------------
    # Content size
    # --------------------------------------

    width = item.get(
        "content_width"
    )

    height = item.get(
        "content_height"
    )

    if (
        width is not None
        and height is not None
    ):

        lines.append(
            f"  サイズ：{width} × {height}"
        )

    return lines


# ==========================================
# Classification Review
# ==========================================

def format_classification_review(item):
    """
    分類確認対象をSlack向けに短く表示する。
    """
    lines = []

    pre_id = item.get("pre_id", "PRE-?????")
    title = item.get("title", "タイトルなし")
    url = item.get("url", "")

    link = f"<{url}|{title}>" if url else title
    lines.append(f"・{pre_id} {link}")

    scores = item.get("classification_scores", {})
    if isinstance(scores, dict):
        ranked = sorted(
            scores.items(),
            key=lambda pair: pair[1],
            reverse=True,
        )
        ranked = [
            (name, score)
            for name, score in ranked
            if isinstance(score, (int, float)) and score > 0
        ][:3]

        if ranked:
            score_text = " / ".join(
                f"{name} {score}"
                for name, score in ranked
            )
            lines.append(f"  候補：{score_text}")

    confidence = item.get("classification_confidence")
    if confidence:
        lines.append(f"  信頼度：{confidence}")

    evidence = item.get("classification_evidence", [])
    evidence_labels = []

    if isinstance(evidence, list):
        for evidence_item in evidence:
            if not isinstance(evidence_item, dict):
                continue

            label = evidence_item.get("evidence")
            if not label:
                keyword = evidence_item.get("keyword")
                field = evidence_item.get("field")
                if keyword:
                    label = f"{field}:{keyword}"
                else:
                    label = str(evidence_item)

            if label not in evidence_labels:
                evidence_labels.append(label)

    if evidence_labels:
        display_evidence = evidence_labels[:5]
        evidence_text = ", ".join(display_evidence)

        if len(evidence_labels) > 5:
            evidence_text += " ..."

        lines.append(f"  根拠：{evidence_text}")

    return lines


def get_review_summary(review_items):
    """
    今回の分類確認対象を、
    ユーザーが最初に把握しやすい大分類へ集計する。

    0件の分類は表示しない。
    """

    summary = {
        "グラフィック": 0,
        "プラグイン": 0,
        "サウンド": 0,
    }

    for item in review_items:
        asset_type = item.get("asset_type")

        if asset_type == "graphic":
            summary["グラフィック"] += 1

        elif asset_type == "plugin":
            summary["プラグイン"] += 1

        elif asset_type == "sound":
            summary["サウンド"] += 1

    return summary


def get_oldest_review_label(review_items):
    """
    確認待ちItemの最古の発生時点をSlack向けに表示する。
    """
    from datetime import datetime, timedelta

    candidates = []

    for item in review_items or []:
        date_text = item.get("created_report_date")
        period = item.get("created_report_period")

        if date_text:
            try:
                dt = datetime.strptime(date_text, "%Y-%m-%d")
                candidates.append((
                    dt,
                    f"{dt.month}/{dt.day} {period or ''}".strip(),
                ))
                continue
            except ValueError:
                pass

        created_at = item.get("created_at")
        if not created_at:
            continue

        try:
            dt = datetime.fromisoformat(created_at)
            if dt.tzinfo is not None:
                dt = dt + timedelta(hours=9)

            hour = dt.hour
            if 5 <= hour < 10:
                inferred_period = "朝"
            elif 10 <= hour < 15:
                inferred_period = "昼"
            elif 15 <= hour < 18:
                inferred_period = "夕"
            else:
                inferred_period = "夜"

            candidates.append((
                dt.replace(tzinfo=None),
                f"{dt.month}/{dt.day} {inferred_period}",
            ))
        except (TypeError, ValueError):
            continue

    if not candidates:
        return None

    candidates.sort(key=lambda pair: pair[0])
    return candidates[0][1]


def format_carryover_pre_ids(carryover_items, max_ranges=5):
    """
    Carryover PRE IDsを連続範囲にまとめ、Slackの冒頭を短く保つ。
    """
    numbers = sorted({
        int(match.group(1))
        for item in (carryover_items or [])
        if isinstance(item, dict)
        for pre_id in [item.get("pre_id")]
        if isinstance(pre_id, str)
        for match in [re.fullmatch(r"PRE-(\d{5})", pre_id)]
        if match
    })

    if not numbers:
        return None

    ranges = []
    start = previous = numbers[0]
    for number in numbers[1:]:
        if number == previous + 1:
            previous = number
            continue
        ranges.append((start, previous))
        start = previous = number
    ranges.append((start, previous))

    def format_range(start_number, end_number):
        first = f"PRE-{start_number:05d}"
        if start_number == end_number:
            return first
        return f"{first}〜PRE-{end_number:05d}"

    if len(ranges) <= max_ranges:
        label = "、".join(format_range(start, end) for start, end in ranges)
    else:
        shown_ranges = ranges[:max_ranges]
        shown_count = sum(end - start + 1 for start, end in shown_ranges)
        shown = "、".join(format_range(start, end) for start, end in shown_ranges)
        label = f"{shown}、ほか{len(numbers) - shown_count}件"

    return f"対象ID：{label}"


def format_review_summary(
    review_items,
    carryover_items=None,
):
    """
    Slack冒頭に表示する分類確認のサマリー。

    今回の新規確認対象と、前回までの持ち越しを分ける。
    """
    review_items = review_items or []
    carryover_items = carryover_items or []

    if not review_items and not carryover_items:
        return []

    lines = [
        "【🔎 要確認】",
    ]

    if review_items:
        summary = get_review_summary(review_items)

        lines.append(
            f"今回：{len(review_items)}件"
        )

        for label in (
            "グラフィック",
            "プラグイン",
            "サウンド",
        ):
            count = summary[label]
            if count:
                lines.append(
                    f"・{label}分類：{count}件"
                )

    if carryover_items:
        lines.append("")
        lines.append("【⏳ 前回までの持ち越し】")
        lines.append(f"{len(carryover_items)}件")

        pre_id_summary = format_carryover_pre_ids(carryover_items)
        if pre_id_summary:
            lines.append(f"・{pre_id_summary}")

        oldest = get_oldest_review_label(
            carryover_items
        )
        if oldest:
            lines.append(
                f"最古：{oldest}"
            )

    lines.append(
        "詳細は下記「分類確認」を確認してください。"
    )

    return lines



def format_source_check_metadata(item):
    """Source Checkのサイト属性を短い表示用文字列にする。"""
    details = []

    resource_types = item.get("resource_types", [])
    if isinstance(resource_types, str):
        resource_types = [resource_types]
    if isinstance(resource_types, list):
        clean_types = [
            value.strip()
            for value in resource_types
            if isinstance(value, str) and value.strip()
        ]
        if clean_types:
            details.append("対象：" + "・".join(dict.fromkeys(clean_types)))

    language = item.get("language")
    if isinstance(language, str) and language.strip():
        details.append("主な言語：" + language.strip())

    site_type = item.get("site_type")
    if isinstance(site_type, str) and site_type.strip():
        details.append("サイト種別：" + site_type.strip())

    return " / ".join(details)


def format_reference_sites(sites=None):
    """
    毎回表示する公式情報リンクと、手動確認用の参考サイト一覧を表示する。
    """
    if sites is None:
        sites = SOURCE_CHECK_SITES

    manual_sites = [
        site for site in sites
        if isinstance(site, dict) and site.get("reference_only")
    ]

    lines = [
        "────────────────────",
        "【📢 Official Information】",
    ]

    for name, url in OFFICIAL_INFORMATION_LINKS:
        lines.append(f"・<{url}|{name}>")

    if not manual_sites:
        return lines

    lines.extend([
        "",
        "────────────────────",
        "【📚 素材・プラグイン関連サイト一覧】",
        "個別の素材・プラグインを自動抽出していないサイトの一覧です。対象分野・主な言語から、確認したいサイトを選べます。",
        "ページ変化を検知できたサイトは、上の「SOURCE CHECK：ページ変化」にも掲載します。",
    ])

    for site in manual_sites:
        name = site.get("name", "名称不明")
        url = site.get("url", "")
        if url:
            lines.append(f"・<{url}|{name}>")
        else:
            lines.append(f"・{name}")

        metadata = format_source_check_metadata(site)
        if metadata:
            lines.append(f"  {metadata}")

    return lines


def format_source_health_warnings(source_results=None):
    """
    Show only partial or failed collectors in the Slack report.
    Successful collectors are omitted to keep routine reports concise.
    """
    lines = []

    display_names = {
        "official_source_check": "Source Check",
    }

    for result in source_results or []:
        if not isinstance(result, dict):
            continue

        name = result.get("name", "unknown")
        display_name = display_names.get(name, name)
        status = result.get("status")

        if status == "PARTIAL":
            summary = result.get("summary") or {}
            request_stats = result.get("request_stats") or {}
            if summary.get("checked") or summary.get("failed"):
                checked = summary.get("checked", 0)
                failed = summary.get("failed", 0)
                total = checked + failed
                detail = f"確認 {checked}/{total}、失敗 {failed}件"
            else:
                detail = (
                    f"HTTP成功 {request_stats.get('succeeded', 0)}件、"
                    f"失敗 {request_stats.get('failed', 0)}件"
                )
            lines.append(f"・{display_name}：一部失敗 （{detail}）")
        elif status == "ERROR":
            error_type = result.get("error_type")
            request_stats = result.get("request_stats") or {}
            if error_type:
                detail = error_type
            else:
                detail = (
                    f"HTTP成功 {request_stats.get('succeeded', 0)}件、"
                    f"失敗 {request_stats.get('failed', 0)}件"
                )
            lines.append(f"・{display_name}：取得失敗（{detail}）")

    if not lines:
        return []

    return ["【⚠️ 収集元の取得状況】"] + lines


