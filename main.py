import feedparser
import json
import requests
import os

from common import load_seen, load_seen_file
from common import save_seen, save_seen_file

import reddit_source

from bs4 import BeautifulSoup

from pathlib import Path
from datetime import datetime, timedelta

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

def classify_official(title):

    title_lower = title.lower()

    if "unite" in title_lower:
        return "UNITE"

    if (
        "forum" in title_lower
        or "yanfly" in title_lower
        or "migration" in title_lower
        or "archive" in title_lower
    ):
        return "Forum重要事項"

    return "本体ニュース"

def load_seen_file(filename):
    path = Path(filename)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

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

def get_official_news_items(seen):

    url = "https://rpgmakerofficial.com/news/"
    new_seen = seen.copy()
    adopted_items = []

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

        for tag in soup.find_all("h3"):
            print("------")
            print(tag)
            print("------")
            
            title = tag.get_text(strip=True)

            if not title:
                continue

            if title in seen:
                continue

            new_seen.append(title)

            category = classify_official(title)

            adopted_items.append(
                {
                    "title": title,
                    "url": url,
                    "category": category,
                }
            )

        print(
            "Official News articles:",
            len(adopted_items)
        )

        for item in adopted_items[:10]:
            print("[Official]", item["title"])

    except Exception as e:

        print(
            "Official News error:",
            str(e)
        )

    print(
        "Official News new:",
        len(adopted_items)
    )

    return adopted_items, new_seen

def main():

    seen = load_seen()

    reddit_items, new_seen = reddit_source.get_reddit_items(seen)

    official_seen = load_seen_file(
        SEEN_OFFICIAL_FILE
    )

    official_items, new_official_seen = (
        get_official_news_items(
            official_seen
        )
    )

    adopted_items = (
        reddit_items
        + official_items
    )

    save_seen(new_seen)

    save_seen_file(
        SEEN_OFFICIAL_FILE,
        new_official_seen
    )

    print("採用件数:", len(adopted_items))
    print("seen登録数:", len(new_seen))

    report = build_report(adopted_items)

    print()
    print("----- REPORT -----")
    print(report)

    send_to_slack(report)


if __name__ == "__main__":
    main()
