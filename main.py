import feedparser
import json
import requests
import os

from pathlib import Path
from datetime import datetime

RSS_URL = "https://www.reddit.com/r/RPGMaker/.rss"

SEEN_FILE = "seen.json"

QUESTION_WORDS = [
    "help",
    "need help",
    "looking for",
    "question",
    "how to",
    "how do",
    "can i",
    "which",
    "what",
]

IGNORE_WORDS = [
    "screenshot saturday",
    "megathread",
    "weekly thread",
]


def classify(title):
    title_lower = title.lower()

    for word in IGNORE_WORDS:
        if word in title_lower:
            return None

    for word in QUESTION_WORDS:
        if word in title_lower:
            return None

    game_keywords = [
        "released",
        "release",
        "steam page",
        "trailer",
        "demo",
        "now out",
        "available now",
        "launch",
        "launched",
    ]

    for keyword in game_keywords:
        if keyword in title_lower:
            return "RPGツクール製ゲーム"

    if "plugin" in title_lower:
        return "プラグイン"

    graphic_keywords = [
        "tileset",
        "sprite",
        "asset pack",
        "character generator",
    ]

    for keyword in graphic_keywords:
        if keyword in title_lower:
            return "グラフィック"

    sound_keywords = [
        "bgm",
        "music pack",
        "sound pack",
        "audio asset",
    ]

    for keyword in sound_keywords:
        if keyword in title_lower:
            return "サウンド"

    tips_keywords = [
        "tutorial",
        "guide",
        "tips",
    ]

    for keyword in tips_keywords:
        if keyword in title_lower:
            return "Tips"

    return None


def load_seen():
    path = Path(SEEN_FILE)

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_seen(data):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_period():
    hour = datetime.now().hour

    if hour < 12:
        return "朝"

    return "夜"


def build_report(items):

    now = datetime.now()

    date_str = now.strftime("%Y.%m.%d")

    period = get_period()

    if len(items) == 0:
        return f"{date_str} {period} → 新着なし"

    categories = {
        "RPGツクール製ゲーム": [],
        "プラグイン": [],
        "グラフィック": [],
        "サウンド": [],
        "Tips": [],
    }

    for item in items:
        categories[item["category"]].append(item)

    report = []

    report.append(f"{date_str} {period} Daily Report")

    report.append(
        f"★★★ U2U(0) / UNITE(0) / 本体ニュース(0)"
    )

    report.append(
        f"★★☆ グラフィック({len(categories['グラフィック'])}) / "
        f"サウンド({len(categories['サウンド'])}) / "
        f"プラグイン({len(categories['プラグイン'])}) / "
        f"Tips({len(categories['Tips'])})"
    )

    report.append(
        f"★☆☆ RPGツクール製ゲーム({len(categories['RPGツクール製ゲーム'])})"
    )

    report.append("")

    order = [
        "グラフィック",
        "サウンド",
        "プラグイン",
        "Tips",
        "RPGツクール製ゲーム",
    ]

    for category in order:

        if len(categories[category]) == 0:
            continue

        report.append(f"【{category}】")

        for item in categories[category]:

            report.append(
                f"<{item['url']}|{item['title']}>"
            )

        report.append("")

    return "\n".join(report)


def send_to_slack(message):

    webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    if not webhook_url:
        print("SLACK_WEBHOOK_URL がありません")
        return

    payload = {
        "text": message
    }

    response = requests.post(
        webhook_url,
        json=payload,
        timeout=30
    )

    print("Slack status:", response.status_code)


def main():

    seen = load_seen()

    feed = feedparser.parse(RSS_URL)

    print("取得件数:", len(feed.entries))

    new_seen = seen.copy()

    adopted_items = []

    for entry in feed.entries:

        url = entry.link

        if url in seen:
            continue

        new_seen.append(url)

        category = classify(entry.title)

        if category:

            adopted_items.append(
                {
                    "title": entry.title,
                    "url": url,
                    "category": category,
                }
            )

            print(f"[採用][{category}] {entry.title}")

    save_seen(new_seen)

    print("採用件数:", len(adopted_items))
    print("seen登録数:", len(new_seen))

    report = build_report(adopted_items)

    print()
    print("----- REPORT -----")
    print(report)

    send_to_slack(report)


if __name__ == "__main__":
    main()
