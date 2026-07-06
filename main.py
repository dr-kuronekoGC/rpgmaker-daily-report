import feedparser
import json
import requests
import os

from bs4 import BeautifulSoup

from pathlib import Path
from datetime import datetime

RSS_URL = "https://www.reddit.com/r/RPGMaker/.rss"
SEEN_FILE = "seen.json"
SEEN_OFFICIAL_FILE = "seen_official.json"
OFFICIAL_NEWS_URL = ""

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

    question_words = QUESTION_WORDS + [
        "thoughts?",
        "any suggestions",
        "recommendation",
        "recommendations",
    ]

    for word in question_words:
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
        "steam store page",
    ]

    for keyword in game_keywords:
        if keyword in title_lower:
            return "RPGツクール製ゲーム"

    plugin_keywords = [
        "plugin",
        "script",
        "system plugin",
        "plugin finder",
    ]

    for keyword in plugin_keywords:
        if keyword in title_lower:
            return "プラグイン"

    graphic_keywords = [
        "tileset",
        "sprite",
        "asset pack",
        "character generator",
        "animation asset",
        "portrait",
        "battler",
        "faceset",
        "character sheet",
    ]

    for keyword in graphic_keywords:
        if keyword in title_lower:
            return "グラフィック"

    sound_keywords = [
        "bgm",
        "music pack",
        "sound pack",
        "audio asset",
        "music",
        "sound effect",
        "sfx",
        "ambient",
    ]

    for keyword in sound_keywords:
        if keyword in title_lower:
            return "サウンド"

    tips_keywords = [
        "tutorial",
        "guide",
        "tips",
        "workflow",
        "how i made",
        "devlog",
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


def get_reddit_items(seen):

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

    return adopted_items, new_seen


def build_report(items):

    now = datetime.now()

    date_str = now.strftime("%Y.%m.%d")

    period = get_period()

    if len(items) == 0:
        return f"{date_str} {period} → 新着なし"

    categories = {
        "本体ニュース": [],
        "RPGツクール製ゲーム": [],
        "プラグイン": [],
        "グラフィック": [],
        "サウンド": [],
        "Tips": [],
    }

    for item in items:
        categories[item["category"]].append(item)

    report = [
        f"{date_str} {period} Daily Report"
    ]

    star3 = []

    if categories["本体ニュース"]:
        star3.append(
            f"本体ニュース({len(categories['本体ニュース'])})"
        )

    if star3:
        report.append(
            "　★★★ " + "、".join(star3)
        )

    star2 = []

    if categories["グラフィック"]:
        star2.append(
            f"グラフィック({len(categories['グラフィック'])})"
        )

    if categories["サウンド"]:
        star2.append(
            f"サウンド({len(categories['サウンド'])})"
        )

    if categories["プラグイン"]:
        star2.append(
            f"プラグイン({len(categories['プラグイン'])})"
        )

    if categories["Tips"]:
        star2.append(
            f"Tips({len(categories['Tips'])})"
        )

    if star2:
        report.append(
            "　★★☆ " + "、".join(star2)
        )

    star1 = []

    if categories["RPGツクール製ゲーム"]:
        star1.append(
            f"RPGツクール製ゲーム({len(categories['RPGツクール製ゲーム'])})"
        )

    if star1:
        report.append(
            "　★☆☆ " + "、".join(star1)
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

        if not categories[category]:
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
        timeout=30,
    )

    print("Slack status:", response.status_code)

def get_official_news_items():

    url = "https://rpgmakerofficial.com/news/"

    try:

        response = requests.get(
            url,
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        items = []

        for tag in soup.find_all("h3"):

            title = tag.get_text(strip=True)

            if not title:
                continue

            items.append(title)

        print(
            "Official News articles:",
            len(items)
        )

        for title in items[:10]:

            print("[Official]", title)

    except Exception as e:

        print(
            "Official News error:",
            str(e)
        )

    return []

def main():

    seen = load_seen()

    reddit_items, new_seen = get_reddit_items(seen)

    official_items = get_official_news_items()

    adopted_items = (
        reddit_items
        + official_items
    )

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
