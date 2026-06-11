import feedparser

RSS_URL = "https://www.reddit.com/r/RPGMaker/.rss"

feed = feedparser.parse(RSS_URL)

IGNORE_WORDS = [
    "screenshot saturday",
    "megathread",
    "what version",
    "help",
    "question",
    "bug",
    "issue",
]

CATEGORIES = {
    "RPGツクール製ゲーム": [
        "released",
        "release",
        "launch",
        "launched",
        "steam",
        "trailer",
        "demo",
        "my game",
        "our game",
    ],
    "プラグイン": [
        "plugin",
        "script",
        "battle system",
        "extension",
    ],
    "グラフィック": [
        "tileset",
        "sprite",
        "character",
        "portrait",
        "face",
        "asset",
    ],
    "サウンド": [
        "bgm",
        "music",
        "sound",
        "audio",
        "ost",
        "sfx",
        "se",
    ],
    "Tips": [
        "tutorial",
        "guide",
        "tips",
        "how to",
    ],
}


def classify(title):
    title_lower = title.lower()

    # 除外判定
    for word in IGNORE_WORDS:
        if word in title_lower:
            return None

    # カテゴリ判定
    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in title_lower:
                return category

    return None


print("取得件数:", len(feed.entries))
print()

adopted = 0

for entry in feed.entries:
    category = classify(entry.title)

    if category:
        adopted += 1
        print(f"[採用][{category}]")
        print(entry.title)
        print()
    else:
        print(f"[除外] {entry.title}")

print()
print("採用件数:", adopted)
