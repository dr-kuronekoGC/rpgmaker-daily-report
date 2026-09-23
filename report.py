import os
import requests

from common import (
    now_jst,
    get_period,
)

from config import (
    REQUEST_TIMEOUT,
    SLACK_WEBHOOK_ENV,
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

        pre_ids = [
            item.get("pre_id")
            for item in carryover_items
            if item.get("pre_id")
        ]

        if pre_ids:
            lines.append(
                "・" + "、".join(pre_ids)
            )

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


def build_report(items, review_items=None, carryover_items=None):

    now = now_jst()

    date_str = now.strftime(
        "%Y.%m.%d"
    )

    period = get_period()

    review_items = review_items or []
    carryover_items = carryover_items or []

    if not items and not review_items and not carryover_items:

        return (
            f"📬 RPG Maker Daily Report\n"
            f"{date_str} {period}\n"
            "\n"
            "新着ニュースはありません。\n"
            "\n"
            "────────────────────\n"
            "【SOURCE CHECK】\n"
            "・<https://www.gamedevmarket.net/|GameDevMarket>"
            " ▶ 素材のセルフチェック"
        )

    categories = {}

    # --------------------------------------
    # Language補完
    # --------------------------------------

    for item in items:

        if item.get("language"):
            continue

        language = detect_language(
            title=item.get(
                "title",
                "",
            ),
            description=item.get(
                "description",
                "",
            ),
            tags=item.get(
                "tags",
                item.get(
                    "source_tags",
                    [],
                ),
            ),
        )

        if language:
            item["language"] = language

    # --------------------------------------
    # カテゴリ整理
    #
    # 分類確認中のItemは通常の掲載欄には出さず、
    # 下部の「分類確認」にまとめる。
    # --------------------------------------

    normal_items = [
        item
        for item in items
        if item.get("classification_status") != "needs_review"
    ]

    for item in normal_items:

        item = item.copy()

        category = item.get(
            "category",
            "",
        )

        display_category = get_display_category(
            category
        )

        item["display_category"] = (
            display_category
        )

        categories.setdefault(
            display_category,
            [],
        ).append(item)

    report = []

    report.append(
        "📬 RPG Maker Daily Report"
    )

    report.append(
        f"{date_str} {period}"
    )

    report.append("")

    # --------------------------------------
    # Classification Review Summary
    # --------------------------------------

    report.extend(
        format_review_summary(
            review_items,
            carryover_items,
        )
    )

    if review_items or carryover_items:
        report.append("")

    # --------------------------------------
    # Summary
    # --------------------------------------

    summary_groups = {
        "今日の注目": [],
        "新作ゲーム": [],
        "プラグイン・素材": [],
        "開発情報・Tips": [],
        "質問・相談": [],
        "Source Check": [],
    }

    for category, category_items in categories.items():

        group = get_report_group(
            category
        )

        if group:

            summary_groups[group].extend(
                category_items
            )

    summary_headers = {
        "今日の注目": "★★★★★ 今日の注目",
        "新作ゲーム": "★★★★☆ 新作ゲーム",
        "プラグイン・素材": "★★★☆☆ プラグイン・素材",
        "開発情報・Tips": "★★☆☆☆ 開発情報・Tips",
        "質問・相談": "★☆☆☆☆ 質問・相談",
        "Source Check": "📡 Source Check",
    }

    for group, group_items in summary_groups.items():

        if not group_items:
            continue

        report.append(
            f"{summary_headers[group]}"
            f"（{len(group_items)}件）"
        )

    report.append("")

    report.append(
        "────────────────────"
    )

    report.append("")

    # --------------------------------------
    # Detail
    # --------------------------------------

    detail_order = [
        "本体ニュース",
        "UNITE",
        "Forum重要事項",
        "プラグイン",
        "グラフィック素材",
        "サウンド素材",
        "ゲーム",
        "Tips",
        "質問",
    ]

    for category in detail_order:

        if category not in categories:
            continue

        report.append(
            f"【{category}】"
        )

        grouped = {}

        for item in categories[category]:

            title = item.get(
                "title",
                "タイトルなし",
            )

            url = item.get(
                "url",
                "",
            )

            source = item.get(
                "source",
                "",
            )

            key = title.lower().strip()

            # ----------------------------------
            # 同一タイトルをまとめる
            # ----------------------------------

            if key not in grouped:

                grouped[key] = {
                    "title": title,
                    "url": url,
                    "sources": [],
                    "items": [],
                }

            if source:

                grouped[key][
                    "sources"
                ].append(
                    source
                )

            grouped[key][
                "items"
            ].append(
                item
            )

        for entry in grouped.values():

            source_labels = []

            for item in entry["items"]:

                source = item.get(
                    "source",
                    "",
                )

                if not source:
                    continue

                language = item.get(
                    "language"
                )

                if language:
                    label = (
                        f"{source}｜{language}"
                    )
                else:
                    label = source

                if label not in source_labels:
                    source_labels.append(
                        label
                    )

            source_text = " / ".join(
                source_labels
            )

            title = entry["title"]
            url = entry["url"]

            # ----------------------------------
            # Slack link
            # ----------------------------------

            link = (
                f"<{url}|{title}>"
                if url
                else title
            )

            if source_text:

                report.append(
                    f"・[{source_text}] {link}"
                )

            else:

                report.append(
                    f"・{link}"
                )

            # ----------------------------------
            # DeviantArt詳細
            #
            # 同一タイトルが複数ソースから
            # 来た場合も、DeviantArtだけを表示。
            # ----------------------------------

            for item in entry["items"]:

                if item.get(
                    "source"
                ) != "DeviantArt":
                    continue

                detail_lines = (
                    format_deviantart_detail(
                        item
                    )
                )

                for detail_line in (
                    detail_lines
                ):

                    report.append(
                        detail_line
                    )

        report.append("")

    # --------------------------------------
    # Classification Review
    # --------------------------------------

    if review_items or carryover_items:
        report.append(
            "────────────────────"
        )
        report.append("")
        report.append(
            f"【🔎 分類確認】（今回：{len(review_items)}件 / 持ち越し：{len(carryover_items)}件）"
        )
        report.append(
            "自動分類に確信がないため、確認待ちです。"
        )
        report.append(
            "回答例：PRE-00152 BGM / PRE-00153 SE / PRE-00154 除外"
        )
        report.append("")

        if carryover_items:
            report.append(
                "持ち越しの詳細は、冒頭のPRE番号から過去レポートを確認してください。"
            )
            report.append(
                "台帳：<https://github.com/dr-kuronekoGC/rpgmaker-daily-report/blob/main/data/review/classification_review.json|classification_review.json>"
            )
            report.append("")

        if review_items:
            report.append("【🆕 今回追加】")
            for item in review_items:
                report.extend(
                    format_classification_review(item)
                )
            report.append("")

    # --------------------------------------
    # Source Check
    # --------------------------------------

    if "SourceCheck" in categories:
        report.append(
            "【SOURCE CHECK】"
        )

        for item in categories["SourceCheck"]:
            title = item.get(
                "title",
                "更新あり",
            )
            url = item.get(
                "url",
                "",
            )

            if url:
                report.append(
                    f"・<{url}|{title}>"
                )
            else:
                report.append(
                    f"・{title}"
                )

        report.append("")


    report.append(
        "────────────────────"
    )

    report.append(
        "【SOURCE CHECK】"
    )

    report.append(
        "・<https://www.gamedevmarket.net/|GameDevMarket>"
        " ▶ 素材のセルフチェック"
    )

    return "\n".join(report)


# ==========================================
# Slack
# ==========================================

def send_to_slack(message):

    webhook_url = os.getenv(
        SLACK_WEBHOOK_ENV
    )

    if not webhook_url:

        print(
            "SLACK_WEBHOOK_URL がありません"
        )

        return False

    response = requests.post(
        webhook_url,
        json={
            "text": message
        },
        timeout=REQUEST_TIMEOUT,
    )

    print(
        "Slack status:",
        response.status_code,
    )

    if 200 <= response.status_code < 300:

        return True

    print(
        "Slack送信に失敗しました。"
        f"status={response.status_code}"
    )

    return False
