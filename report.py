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
# Report
# ==========================================

def build_report(items):

    now = now_jst()

    date_str = now.strftime("%Y.%m.%d")

    period = get_period()

    if not items:
        return f"{date_str} {period}\n新着ニュースはありません。"

    categories = {}

    for item in items:

        category_info = DISPLAY_CATEGORY.get(
            item["category"],
        )

        if category_info:

            display_category = category_info["group"]

        else:

            display_category = item["category"]

        item = item.copy()

        item["display_category"] = display_category

        categories.setdefault(
            display_category,
            []
        ).append(item)

    report = []

    report.append(
        f"📬 RPG Maker Daily Report"
    )

    report.append(
        f"{date_str} {period}"
    )

    report.append("")

    # ----------------------
    # Summary
    # ----------------------

    for header, group in CATEGORY_GROUPS.items():

        total = sum(
            len(categories[c])
            for c in group
            if c in categories
        )

        if total == 0:
            continue

        report.append(
            f"{header}（{total}件）"
        )

    report.append("")
    report.append("────────────────────")
    report.append("")

    # ----------------------
    # Detail
    # ----------------------

    for category in DISPLAY_ORDER:

        if category not in categories:
            continue

        report.append(f"【{category}】")

        grouped = {}

        for item in categories[category]:

            key = item["title"].lower().strip()

            grouped.setdefault(
                key,
                {
                    "title": item["title"],
                    "url": item["url"],
                    "sources": [],
                },
            )

            grouped[key]["sources"].append(
                item.get("source", "")
            )

        for game in grouped.values():

            source_text = " / ".join(
                sorted(
                    set(game["sources"])
                )
            )

            report.append(
                f"・[{source_text}] <{game['url']}|{game['title']}>"
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
