import html
import re

from config import (
    RPGMAKER_UNION_RESOURCE_URL,
    RPGMAKER_UNION_PLUGIN_URL,
    RPGMAKER_UNION_SEEN_FILE,
)
from sources.base import get_html


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


def clean_text(value):
    if not isinstance(value, str):
        return ""

    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    return " ".join(value.split()).strip()


def extract_tag_value(block, tag_name):
    pattern = (
        r"<"
        + re.escape(tag_name)
        + r"\b[^>]*>(.*?)</"
        + re.escape(tag_name)
        + r">"
    )

    match = re.search(
        pattern,
        block,
        re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return ""

    return clean_text(match.group(1))


def extract_link(block):
    match = re.search(
        r"<link\b[^>]*href=[\"']([^\"']+)",
        block,
        re.IGNORECASE,
    )

    if match:
        return html.unescape(match.group(1)).strip()

    match = re.search(
        r"<link\b[^>]*>(.*?)</link>",
        block,
        re.IGNORECASE | re.DOTALL,
    )

    if match:
        return clean_text(match.group(1))

    return ""


def extract_entries(raw):
    start_pattern = re.compile(
        r"<(?:item|entry)\b[^>]*>",
        re.IGNORECASE,
    )

    starts = list(start_pattern.finditer(raw))
    entries = []

    for index, match in enumerate(starts):
        start = match.start()

        if index + 1 < len(starts):
            end = starts[index + 1].start()
        else:
            end = len(raw)

        block = raw[start:end]

        title = extract_tag_value(
            block,
            "title",
        )
        url = extract_link(block)

        if not title or not url:
            continue

        entries.append(
            {
                "title": title,
                "url": url,
            }
        )

    return entries


def print_rss_diagnostics(section_type, raw):
    counts = {
        "<item": len(re.findall(r"<item\b", raw, re.IGNORECASE)),
        "</item": len(re.findall(r"</item\s*>", raw, re.IGNORECASE)),
        "<entry": len(re.findall(r"<entry\b", raw, re.IGNORECASE)),
        "</entry": len(re.findall(r"</entry\s*>", raw, re.IGNORECASE)),
        "<link": len(re.findall(r"<link\b", raw, re.IGNORECASE)),
        "<title": len(re.findall(r"<title\b", raw, re.IGNORECASE)),
        "/thread/": len(re.findall(r"/thread/", raw, re.IGNORECASE)),
    }

    print(
        f"[{SOURCE_NAME}][DEBUG] {section_type} RSS diagnostics: "
        f"length={len(raw)}, "
        f"item_start={counts['<item']}, "
        f"item_end={counts['</item']}, "
        f"entry_start={counts['<entry']}, "
        f"entry_end={counts['</entry']}, "
        f"link={counts['<link']}, "
        f"title={counts['<title']}, "
        f"thread={counts['/thread/']}"
    )

    if not raw.strip():
        print(
            f"[{SOURCE_NAME}][DEBUG] "
            f"{section_type} RSS is empty"
        )
        return

    preview = " ".join(raw[:500].split())
    print(
        f"[{SOURCE_NAME}][DEBUG] "
        f"{section_type} RSS preview: {preview}"
    )

    thread_matches = re.findall(
        r"/thread/[^"'<>s]+",
        raw,
        re.IGNORECASE,
    )

    if thread_matches:
        print(
            f"[{SOURCE_NAME}][DEBUG] "
            f"{section_type} first thread URL: "
            f"{html.unescape(thread_matches[0])}"
        )


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
            raw = get_html(feed_url)
        except Exception as e:
            print(
                f"[{SOURCE_NAME}] "
                f"{section_type} RSS error: {e}"
            )
            continue

        entries = extract_entries(raw)

        print(
            f"[{SOURCE_NAME}] "
            f"{section_type} RSS: "
            f"{len(entries)} items"
        )

        if not entries:
            print_rss_diagnostics(
                section_type,
                raw,
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
