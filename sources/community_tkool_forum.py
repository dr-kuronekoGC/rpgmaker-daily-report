import feedparser

from config import (
    TKOOL_FORUM_RSS,
    TKOOL_FORUM_SEEN_FILE,
)

SEEN_FILE = TKOOL_FORUM_SEEN_FILE
SOURCE_NAME = "ツクールフォーラム"

PLUGIN_KEYWORDS = (
    "プラグイン",
    "plugin",
    "plugins",
    "script",
    "javascript",
    "js",
)

SOUND_KEYWORDS = (
    "音素材",
    "音楽",
    "bgm",
    "bgs",
    "se",
    "sound",
    "audio",
)

GRAPHIC_KEYWORDS = (
    "素材",
    "画像",
    "グラフィック",
    "キャラ",
    "キャラクター",
    "立ち絵",
    "顔グラ",
    "歩行グラ",
    "タイル",
    "tileset",
    "sprite",
    "icon",
    "背景",
)

TIPS_KEYWORDS = (
    "tutorial",
    "tips",
    "tip",
    "講座",
    "チュートリアル",
    "ノウハウ",
    "解説",
    "制作方法",
    "作り方",
)

QUESTION_KEYWORDS = (
    "質問",
    "教えて",
    "わからない",
    "分からない",
    "できますか",
    "方法を知りたい",
    "help",
    "question",
    "request",
)

IGNORE_FORUM_KEYWORDS = (
    "q&a",
    "作品紹介",
    "雑談",
)


def normalize_text(value):
    if not isinstance(value, str):
        return ""
    return " ".join(value.lower().split())


def get_entry_forum_name(entry):
    tags = entry.get("tags", [])

    names = []

    for tag in tags:
        if isinstance(tag, dict):
            term = tag.get("term")
            if isinstance(term, str):
                names.append(term.strip())

    categories = entry.get("categories", [])

    for category in categories:
        if isinstance(category, str):
            names.append(category.strip())

    return " / ".join(
        name for name in names if name
    )


def classify(title, forum_name):
    title_text = normalize_text(title)
    forum_text = normalize_text(forum_name)

    if any(
        keyword in title_text
        for keyword in QUESTION_KEYWORDS
    ):
        return None

    if any(
        keyword in forum_text
        for keyword in IGNORE_FORUM_KEYWORDS
    ):
        return None

    if any(
        keyword in forum_text
        for keyword in (
            "プラグイン制作",
            "plugins and mods",
            "script",
        )
    ):
        if any(
            keyword in title_text
            for keyword in TIPS_KEYWORDS
        ):
            return "ツクールフォーラムTips"
        return "ツクールフォーラムプラグイン"

    if any(
        keyword in forum_text
        for keyword in (
            "素材制作",
            "素材/プラグイン交換",
            "resources",
        )
    ):
        if any(
            keyword in title_text
            for keyword in SOUND_KEYWORDS
        ):
            return "ツクールフォーラムサウンド素材"

        if any(
            keyword in title_text
            for keyword in PLUGIN_KEYWORDS
        ):
            return "ツクールフォーラムプラグイン"

        if any(
            keyword in title_text
            for keyword in GRAPHIC_KEYWORDS
        ):
            return "ツクールフォーラムグラフィック素材"

        return None

    if any(
        keyword in forum_text
        for keyword in (
            "ニュース",
            "更新情報",
        )
    ):
        return "Forum重要事項"

    if any(
        keyword in title_text
        for keyword in TIPS_KEYWORDS
    ):
        return "ツクールフォーラムTips"

    if any(
        keyword in title_text
        for keyword in PLUGIN_KEYWORDS
    ):
        return "ツクールフォーラムプラグイン"

    if any(
        keyword in title_text
        for keyword in SOUND_KEYWORDS
    ):
        return "ツクールフォーラムサウンド素材"

    if any(
        keyword in title_text
        for keyword in GRAPHIC_KEYWORDS
    ):
        return "ツクールフォーラムグラフィック素材"

    return None


def get_items(seen):
    try:
        feed = feedparser.parse(
            TKOOL_FORUM_RSS
        )

        new_seen = list(seen)
        seen_set = set(seen)
        adopted_items = []

        for entry in feed.entries:
            url = entry.get("link")
            title = entry.get("title", "").strip()

            if not url or not title:
                continue

            if url in seen_set:
                continue

            forum_name = get_entry_forum_name(entry)

            category = classify(
                title,
                forum_name,
            )

            new_seen.append(url)
            seen_set.add(url)

            if category is None:
                continue

            adopted_items.append(
                {
                    "title": title,
                    "url": url,
                    "category": category,
                    "source": SOURCE_NAME,
                }
            )

            print(
                f"[{SOURCE_NAME}]"
                f"[{category}] {title}"
            )

        if not seen:
            print(
                f"[{SOURCE_NAME}] Baseline: "
                f"{len(new_seen)} items"
            )
            return [], new_seen

        print(
            f"[{SOURCE_NAME}] New: "
            f"{len(adopted_items)}"
        )

        return adopted_items, new_seen

    except Exception as e:
        print(
            f"[{SOURCE_NAME}] Error: {e}"
        )
        return [], seen
