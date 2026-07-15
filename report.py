import os
import requests

from common import now_jst, get_period
from config import (
    REQUEST_TIMEOUT,
    SLACK_WEBHOOK_ENV,
)

# ==========================================
# Category Display
# ==========================================

CATEGORY_GROUPS = {
    "★★★": [
        "本体ニュース",
        "UNITE",
        "Forum重要事項",
    ],
    "★★☆": [
        "Forum",          # ←追加
        "プラグイン",
        "Tips",
        "グラフィック",
        "サウンド",
    ],
    "★☆☆": [
        "RPGツクール製ゲーム",
    ],
}

DISPLAY_ORDER = [
    category
    for categories in CATEGORY_GROUPS.values()
    for category in categories
]


# ==========================================
# Report
# ==========================================

def build_report(items):

    now = now_jst()

    date_str = now.strftime("%Y.%m.%d")

    period = get_period()

    if not items:
        return f"{date_str} {period} → 新着なし"

    categories = {}

    for item in items:

        categories.setdefault(
            item["category"],
            []
        ).append(item)

    report = [
        f"{date_str} {period} Daily Report"
    ]

    # --------------------------
    # Summary
    # --------------------------

    for stars, group in CATEGORY_GROUPS.items():

        summary = []

        for category in group:

            if category in categories:

                summary.append(
                    f"{category}({len(categories[category])})"
                )

        if summary:

            report.append(
                f"　{stars} " + "、".join(summary)
            )

    report.append("────────────────────")
    report.append("")

    # --------------------------
    # Detail
    # --------------------------

    for category in DISPLAY_ORDER:

        if category not in categories:
            continue

        report.append(f"【{category}】")

        for item in categories[category]:

            report.append(
                f"<{item['url']}|{item['title']}>"
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
