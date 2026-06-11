import feedparser
import json
from pathlib import Path

RSS_URL = "https://www.reddit.com/r/RPGMaker/.rss"

SEEN_FILE = "seen.json"

IGNORE_WORDS = [
    "screenshot saturday",
    "megathread",
]

CATEGORIES = {
    "RPGツクール製ゲーム": [
        "released",
        "release",
        "trailer",
        "steam page",
        "demo",
        "now out",
    ],
    "プラグイン": [
        "plugin",
    ],
    "グラフィック": [
        "tileset",
        "sprite",
        "asset pack",
        "character generator",
    ],
    "サウンド": [
        "bgm",
        "music pack",
        "sound pack",
        "audio asset",
    ],
    "Tips": [
        "tutorial",
        "guide",
        "tips",
    ],
}


def load_seen():
    path = Path(SEEN_FILE)

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_seen(data):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def classify(title):
    title_lower = title.lower()

    # 除外ワード
    for word in IGNORE_WORDS:
        if word in title_lower:
            return None

    # 質問系除外
    if (
        title_lower.startswith("what ")
        or title_lower.startswith("which ")
        or title_lower.startswith("how ")
        or title_lower.startswith("can i ")
        or title_lower.startswith("need ")
        or title_lower.startswith("looking for ")
    ):
        return None

    # カテゴリ判定
    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in title_lower:
                return category

    return None


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
