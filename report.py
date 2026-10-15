from common import (
    now_jst,
    get_period,
)

from report_formatters import (
    CATEGORY_GROUPS,
    DISPLAY_ORDER,
    format_carryover_pre_ids,
    format_classification_review,
    format_deviantart_detail,
    format_reference_sites,
    format_review_summary,
    format_source_check_metadata,
    format_source_health_warnings,
    get_display_category,
    get_oldest_review_label,
    get_report_group,
    get_review_summary,
)
from slack_client import send_to_slack


def build_report(items, review_items=None, carryover_items=None, source_results=None):

    now = now_jst()

    date_str = now.strftime(
        "%Y.%m.%d"
    )

    period = get_period()

    review_items = review_items or []
    carryover_items = carryover_items or []

    source_health_lines = format_source_health_warnings(
        source_results
    )

    if not items and not review_items and not carryover_items:
        report_lines = [
            "📬 RPG Maker Daily Report",
            f"{date_str} {period}",
            "",
            "新着ニュースはありません。",
        ]

        if source_health_lines:
            report_lines.extend([""] + source_health_lines)

        report_lines.extend([""] + format_reference_sites())
        return "\n".join(report_lines)

    categories = {}

    # --------------------------------------
    # Language補完
    # --------------------------------------

    for item in items:

        if item.get("language"):
            continue

        # Source Check titles are generated Japanese status labels,
        # not titles from the monitored site. Do not infer language from them.
        if (
            item.get("source") == "Source Check"
            or item.get("category") == "SourceCheck"
        ):
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

    if source_health_lines:
        report.extend(source_health_lines)
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
            "【SOURCE CHECK：ページ変化】"
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

            metadata = format_source_check_metadata(item)
            if metadata:
                report.append(f"  {metadata}")

        report.append("")


    report.extend(
        format_reference_sites()
    )

    return "\n".join(report)
