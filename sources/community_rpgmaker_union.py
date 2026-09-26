import feedparser

from config import (
    RPGMAKER_UNION_RESOURCE_URL,
    RPGMAKER_UNION_PLUGIN_URL,
    RPGMAKER_UNION_SEEN_FILE,
)


SEEN_FILE = RPGMAKER_UNION_SEEN_FILE
SOURCE_NAME = "RPG Maker Union"


SECTION_FEEDS = (
    (
        RPGMAKER_UNION_RESOURCE_URL.rstrip("/") + "/index.rss",
        "resource",
    ),
    (
        RPGMAKER_UNION_PLUGIN_URL.rstrip("/") + "/index.rss",
        "plugin",
    ),
)


QUESTION_KEYWORDS = (
    "ищу",
    "ищем",
    "нужен",
    "нужна",
    "нужно",
    "нужны",
    "поиск",
    "помощь",
    "вопрос",
    "просьба",
    "запрос",
    "как сделать",
    "как создать",
)


SOUND_KEYWORDS = (
    "музык",
    "звук",
    "аудио",
    "bgm",
    "bgs",
    "sfx",
)


def normalize_text(value):
    if not isinstance(value, str):
        return ""

    return " ".join(value.lower().split())


def classify(title, section_type):
    text = normalize_text(title)

    if any(
        keyword in text
        for keyword in QUESTION_KEYWORDS
    ):
        return None

    if section_type == "plugin":
        return "プラグイン"

    if any(
        keyword in text
        for keyword in SOUND_KEYWORDS
    ):
        return "サウンド素材"

    return "グラフィック素材"


def get_items(seen):
    new_seen = list(seen)
    seen_set = set(seen)
    adopted_items = []

    for feed_url, section_type in SECTION_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            print(
                f"[{SOURCE_NAME}] "
                f"{section_type} RSS error: {e}"
            )
            continue

        if feed.bozo and not feed.entries:
            print(
                f"[{SOURCE_NAME}] "
                f"{section_type} RSS error: "
                f"{feed.bozo_exception}"
            )
            continue

        print(
            f"[{SOURCE_NAME}] "
            f"{section_type} RSS: "
            f"{len(feed.entries)} items"
        )

        for entry in feed.entries:
            url = entry.get("link")
            title = entry.get(
                "title",
                "",
            ).strip()

            if not url or not title:
                continue

            if url in seen_set:
                continue

            new_seen.append(url)
            seen_set.add(url)

            category = classify(
                title,
                section_type,
            )

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
                f"[{category}] "
                f"{title}"
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
