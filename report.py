import os
import requests

from common import now_jst, get_period
from config import (
    REQUEST_TIMEOUT,
    SLACK_WEBHOOK_ENV,
)

def build_report(items):

    now = now_jst()

    date_str = now.strftime("%Y.%m.%d")

    period = get_period()

    if len(items) == 0:
        return f"{date_str} {period} → 新着なし"

    categories = {}

    for item in items:

        category = item["category"]

        if category not in categories:
            categories[category] = []

        categories[category].append(item)

    report = [
        f"{date_str} {period} Daily Report"
    ]

    # ----------------------------
    # ★★★
    # ----------------------------

    star3_order = [
        "本体ニュース",
        "UNITE",
        "Forum重要事項",
    ]

    star3 = []

    for category in star3_order:

        if category in categories:
            star3.append(
                f"{category}({len(categories[category])})"
            )

    if star3:

        report.append(
            "　★★★ " + "、".join(star3)
        )

    # ----------------------------
    # ★★☆
    # ----------------------------

    star2_order = [
        "プラグイン",
        "Tips",
        "グラフィック",
        "サウンド",
    ]

    star2 = []

    for category in star2_order:

        if category in categories:
            star2.append(
                f"{category}({len(categories[category])})"
            )

    if star2:

        report.append(
            "　★★☆ " + "、".join(star2)
        )

    # ----------------------------
    # ★☆☆
    # ----------------------------

    star1_order = [
        "RPGツクール製ゲーム",
    ]

    star1 = []

    for category in star1_order:

        if category in categories:
            star1.append(
                f"{category}({len(categories[category])})"
            )

    if star1:

        report.append(
            "　★☆☆ " + "、".join(star1)
        )

    report.append("────────────────────")

    report.append("")

    display_order = [
        "本体ニュース",
        "UNITE",
        "Forum重要事項",
        "プラグイン",
        "Tips",
        "グラフィック",
        "サウンド",
        "RPGツクール製ゲーム",
    ]

    for category in display_order:

        if category not in categories:
            continue

        report.append(f"【{category}】")

        for item in categories[category]:

            report.append(
                f"<{item['url']}|{item['title']}>"
            )

        report.append("")

    return "\n".join(report)


def send_to_slack(message):

    webhook_url = os.getenv(
        SLACK_WEBHOOK_ENV
    )

    if not webhook_url:

        print("SLACK_WEBHOOK_URL がありません")

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
        response.status_code
    )
