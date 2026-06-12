import feedparser
import json
from pathlib import Path

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

    # 完全除外
    for word in IGNORE_WORDS:
        if word in title_lower:
            return None

    # 質問系除外
    for word in QUESTION_WORDS:
        if word in title_lower:
            return None

    # RPGツクール製ゲーム
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

    # プラグイン
    if "plugin" in title_lower:
        return "プラグイン"

    # グラフィック
    graphic_keywords = [
        "tileset",
        "sprite",
        "asset pack",
        "character generator",
    ]

    for keyword in graphic_keywords:
        if keyword in title_lower:
            return "グラフィック"

    # サウンド
    sound_keywords = [
        "bgm",
        "music pack",
        "sound pack",
        "audio asset",
    ]

    for keyword in sound_keywords:
        if keyword in title_lower:
            return "サウンド"

    # Tips
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


seen = load_seen()

feed = feedparser.parse(RSS_URL)

print("取得件数:", len(feed.entries))
print()

new_seen = seen.copy()

adopted = 0

for entry in feed.entries:

    url = entry.link

    if url in seen:
        continue

    new_seen.append(url)

    category = classify(entry.title)

    if category:
        adopted += 1

        print(f"[採用][{category}]")
        print(entry.title)
        print(url)
        print()

save_seen(new_seen)

print("採用件数:", adopted)
print("seen登録数:", len(new_seen))
