import html
import json
import re

from config import (
    RPGMAKER_UNION_RESOURCE_URL,
    RPGMAKER_UNION_PLUGIN_URL,
    RPGMAKER_UNION_SEEN_FILE,
)
from sources.base import get_html


SEEN_FILE = RPGMAKER_UNION_SEEN_FILE
SOURCE_NAME = "RPG Maker Union"


SECTION_PAGES = (
    (
        RPGMAKER_UNION_RESOURCE_URL,
        "resource",
    ),
    (
        RPGMAKER_UNION_PLUGIN_URL,
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


def clean_text(value):
    if not isinstance(value, str):
        return ""

    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    return " ".join(value.split()).strip()


def extract_forum_threads(raw):
    marker = "window.data = "
    marker_pos = raw.find(marker)

    if marker_pos < 0:
        return []

    json_start = marker_pos + len(marker)

    try:
        data, _ = json.JSONDecoder().raw_decode(
            raw[json_start:]
        )
    except json.JSONDecodeError:
        return []

    threads = data.get("forumThreads", [])

    if not isinstance(threads, list):
        return []

    entries = []

    for thread in threads:
        if not isinstance(thread, dict):
            continue

        title = clean_text(thread.get("title", ""))
        url = thread.get("viewUrl", "")
        thread_id = thread.get("id")

        if not title or not url:
            continue

        if not url.startswith("/thread/"):
            continue

        full_url = (
            "https://rpgmakerunion.ru"
            + url
        )

        entries.append(
            {
                "title": title,
                "url": full_url,
                "source_item_id": (
                    str(thread_id)
                    if thread_id is not None
                    else url
                ),
            }
        )

    return entries


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

    for page_url, section_type in SECTION_PAGES:
        try:
            raw = get_html(page_url)
        except Exception as e:
            print(
                f"[{SOURCE_NAME}] "
                f"{section_type} page error: {e}"
            )
            continue

        entries = extract_forum_threads(raw)

        print(
            f"[{SOURCE_NAME}] "
            f"{section_type} page: "
            f"{len(entries)} threads"
        )

        if not entries:
            print(
                f"[{SOURCE_NAME}] "
                f"{section_type} page: "
                f"no structured thread data"
            )

        for entry in entries:
            url = entry["url"]
            title = entry["title"]

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
                    "source_item_id": entry[
                        "source_item_id"
                    ],
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
