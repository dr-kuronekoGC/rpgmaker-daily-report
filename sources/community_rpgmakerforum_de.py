import feedparser

from config import (
    RPGMAKERFORUM_DE_RSS,
    RPGMAKERFORUM_DE_SEEN_FILE,
)

SEEN_FILE = RPGMAKERFORUM_DE_SEEN_FILE
SOURCE_NAME = "RPG Maker Forum DE"

PLUGIN_KEYWORDS = (
    "plugin",
    "plugins",
    "script",
    "javascript",
    "js",
)

SOUND_KEYWORDS = (
    "sound",
    "audio",
    "musik",
    "musik素材",
    "bgm",
    "bgs",
    "sfx",
    "soundeffekt",
    "soundeffekte",
)

GRAPHIC_KEYWORDS = (
    "grafik",
    "grafiken",
    "pixel",
    "pixelart",
    "sprite",
    "sprites",
    "tileset",
    "tilesets",
    "charakter",
    "charaktere",
    "faceset",
    "portrait",
    "animation",
    "bilder",
    "material",
)

TIPS_KEYWORDS = (
    "tutorial",
    "tipps",
    "tips",
    "trick",
    "tricks",
    "guide",
    "anleitung",
    "erklärung",
    "know-how",
    "formel",
    "formeln",
    "damage",
    "mapping",
    "event",
    "events",
    "game design",
)

QUESTION_KEYWORDS = (
    "frage",
    "fragen",
    "hilfe",
    "suchen",
    "suche",
    "wie ",
    "warum ",
    "kann man",
    "kann ich",
    "jemand",
    "wer kann",
    "problem",
    "probleme",
)

IGNORE_FORUM_KEYWORDS = (
    "projektvorstellungen",
    "plauderecke",
    "mitgliedervorstellung",
    "herausforderungen",
)

MATERIAL_FORUM_KEYWORDS = (
    "materialien",
    "materialsammlung",
)

TUTORIAL_FORUM_KEYWORDS = (
    "rpg-maker-tutorials",
)

PLUGIN_FORUM_KEYWORDS = (
    "plugins",
    "plugin",
    "script",
    "scripts",
)

NEWS_FORUM_KEYWORDS = (
    "news",
    "neuigkeiten",
)


def normalize_text(value):
    if not isinstance(value, str):
        return ""
    return " ".join(value.lower().split())


def get_entry_categories(entry):
    names = []

    for tag in entry.get("tags", []):
        if isinstance(tag, dict):
            term = tag.get("term")
            if isinstance(term, str):
                names.append(term.strip())

    for category in entry.get("categories", []):
        if isinstance(category, str):
            names.append(category.strip())

    return " / ".join(
        name for name in names if name
    )


def contains_any(text, keywords):
    return any(
        keyword in text
        for keyword in keywords
    )


def classify(title, forum_name):
    title_text = normalize_text(title)
    forum_text = normalize_text(forum_name)

    if contains_any(
        title_text,
        QUESTION_KEYWORDS,
    ):
        return None

    if contains_any(
        forum_text,
        IGNORE_FORUM_KEYWORDS,
    ):
        return None

    if contains_any(
        forum_text,
        NEWS_FORUM_KEYWORDS,
    ):
        return "RPG Maker Forum DE重要事項"

    if contains_any(
        forum_text,
        PLUGIN_FORUM_KEYWORDS,
    ):
        if contains_any(
            title_text,
            TIPS_KEYWORDS,
        ):
            return "RPG Maker Forum DETips"
        return "RPG Maker Forum DEプラグイン"

    if contains_any(
        forum_text,
        MATERIAL_FORUM_KEYWORDS,
    ):
        if contains_any(
            title_text,
            SOUND_KEYWORDS,
        ):
            return "RPG Maker Forum DEサウンド素材"

        if contains_any(
            title_text,
            PLUGIN_KEYWORDS,
        ):
            return "RPG Maker Forum DEプラグイン"

        if contains_any(
            title_text,
            GRAPHIC_KEYWORDS,
        ):
            return "RPG Maker Forum DEグラフィック素材"

        return None

    if contains_any(
        forum_text,
        TUTORIAL_FORUM_KEYWORDS,
    ):
        return "RPG Maker Forum DETips"

    if contains_any(
        title_text,
        PLUGIN_KEYWORDS,
    ):
        return "RPG Maker Forum DEプラグイン"

    if contains_any(
        title_text,
        SOUND_KEYWORDS,
    ):
        return "RPG Maker Forum DEサウンド素材"

    if contains_any(
        title_text,
        GRAPHIC_KEYWORDS,
    ):
        return "RPG Maker Forum DEグラフィック素材"

    if contains_any(
        title_text,
        TIPS_KEYWORDS,
    ):
        return "RPG Maker Forum DETips"

    return None


def get_items(seen):
    try:
        feed = feedparser.parse(
            RPGMAKERFORUM_DE_RSS
        )

        new_seen = list(seen)
        seen_set = set(seen)
        adopted_items = []

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

            forum_name = get_entry_categories(
                entry
            )

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

        return (
            adopted_items,
            new_seen,
        )

    except Exception as e:
        print(
            f"[{SOURCE_NAME}] Error: {e}"
        )
        return [], seen
