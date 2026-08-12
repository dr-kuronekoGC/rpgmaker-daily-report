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

    return None


# ==========================================
# Report
# ==========================================

def build_report(items):

    now = now_jst()

    date_str = now.strftime(
        "%Y.%m.%d"
    )

    period = get_period()

    if not items:

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
    # カテゴリ整理
    # --------------------------------------

    for item in items:

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
    # Summary
    # --------------------------------------

    summary_groups = {
        "今日の注目": [],
        "新作ゲーム": [],
        "プラグイン・素材": [],
        "開発情報・Tips": [],
        "質問・相談": [],
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

            grouped.setdefault(
                key,
                {
                    "title": title,
                    "url": url,
                    "sources": [],
                },
            )

            if source:
                grouped[key]["sources"].append(
                    source
                )

        for entry in grouped.values():

            source_text = " / ".join(
                sorted(
                    set(
                        entry["sources"]
                    )
                )
            )

            title = entry["title"]
            url = entry["url"]

            # Slack mrkdwn形式。
            # URLを表示文字列に混ぜない。
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

        report.append("")

    # --------------------------------------
    # Source Check
    # --------------------------------------

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

        return

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
