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
# Report Group
# ==========================================

REPORT_GROUPS = [
    {
        "title": "★★★★★ 今日の注目",
        "groups": ["公式"],
    },
    {
        "title": "★★★★☆ 新作ゲーム",
        "groups": ["ゲーム"],
    },
    {
        "title": "★★★☆☆ プラグイン・素材",
        "groups": [
            "プラグイン",
            "グラフィック素材",
            "サウンド素材",
        ],
    },
    {
        "title": "★★☆☆☆ 開発情報・Tips",
        "groups": ["Tips"],
    },
    {
        "title": "★☆☆☆☆ 質問・相談",
        "groups": ["質問"],
    },
]


# ==========================================
# Category
# ==========================================

def get_display_group(category):

    info = DISPLAY_CATEGORY.get(category)

    if info:
        return info["group"]

    return category


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
            f"{date_str} {period}\n"
            "新着ニュースはありません。"
        )

    categories = {}

    # --------------------------------------
    # 表示グループへ変換
    # --------------------------------------

    for item in items:

        display_group = get_display_group(
            item["category"]
        )

        item = item.copy()

        item["display_group"] = display_group

        categories.setdefault(
            display_group,
            [],
        ).append(item)

    # --------------------------------------
    # Header
    # --------------------------------------

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

    for config in REPORT_GROUPS:

        total = sum(
            len(categories[group])
            for group in config["groups"]
            if group in categories
        )

        if total == 0:
            continue

        report.append(
            f"{config['title']}（{total}件）"
        )

    report.append("")

    report.append(
        "────────────────────"
    )

    report.append("")

    # --------------------------------------
    # Detail
    # --------------------------------------

    for config in REPORT_GROUPS:

        for display_group in config["groups"]:

            if display_group not in categories:
                continue

            report.append(
                f"【{display_group}】"
            )

            grouped = {}

            for item in categories[
                display_group
            ]:

                key = (
                    item["title"]
                    .lower()
                    .strip()
                )

                grouped.setdefault(
                    key,
                    {
                        "title": item["title"],
                        "url": item["url"],
                        "sources": [],
                    },
                )

                source = item.get(
                    "source",
                    "",
                )

                if source:

                    grouped[key][
                        "sources"
                    ].append(source)

            for game in grouped.values():

                source_text = " / ".join(
                    sorted(
                        set(
                            game["sources"]
                        )
                    )
                )

                report.append(
                    f"・[{source_text}] "
                    f"<{game['url']}|"
                    f"{game['title']}>"
                )

            report.append("")

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