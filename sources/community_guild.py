# ==========================================
# RPG Maker Guild
# ==========================================

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import (
    GUILD_URL,
    GUILD_PLUGIN_URL,
    GUILD_SEEN_FILE,
    REQUEST_TIMEOUT,
)


SEEN_FILE = GUILD_SEEN_FILE


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(compatible; RPGMakerDailyReport/1.0)"
    )
}


# ==========================================
# Settings
# ==========================================

MAX_PAGES = 3


# ==========================================
# Classification
# ==========================================

def classify_material(title, tags):
    """
    素材カテゴリをグラフィック／サウンドに分類する。

    判定できない素材は、現時点ではグラフィック素材として扱う。
    Daily Reportではグラフィック素材を優先するため、
    素材投稿の取りこぼしを避ける方針。
    """

    text = " ".join(
        [title] + list(tags)
    ).lower()

    sound_keywords = [
        "bgm",
        "bgs",
        "sound",
        "audio",
        "music",
        "se",
        "sfx",
        "sound effect",
        "sound effects",
        "音楽",
        "bgm素材",
        "se素材",
        "効果音",
        "サウンド",
        "音声",
    ]

    if any(
        keyword in text
        for keyword in sound_keywords
    ):
        return "サウンド素材"

    return "グラフィック素材"


def classify_plugin(title, tags):
    """
    GuildのプラグインカテゴリをDaily Reportの
    「RPG Makerプラグイン」に分類する。
    """

    return "RPG Makerプラグイン"


# ==========================================
# Helpers
# ==========================================

def get_tags(topic):
    tags = []

    for tag in topic.select(
        ".discourse-tag, .discourse-tag.simple"
    ):
        text = tag.get_text(
            " ",
            strip=True,
        )

        if text:
            tags.append(text)

    return tags


def extract_topics(html, category_type):
    """
    Discourseのカテゴリ一覧からトピックを抽出する。
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    items = []

    topic_rows = soup.select(
        "tr.topic-list-item"
    )

    for topic in topic_rows:

        link = topic.select_one(
            "a.title"
        )

        if link is None:
            continue

        href = link.get(
            "href"
        )

        title = link.get_text(
            " ",
            strip=True,
        )

        if not href or not title:
            continue

        url = urljoin(
            GUILD_URL,
            href,
        )

        # Discourseのカテゴリ一覧には、
        # 固定の説明トピックなども含まれるため除外する。
        if not re.search(
            r"/t/[^/]+/\d+",
            url,
        ):
            continue

        tags = get_tags(topic)

        if category_type == "material":
            category = classify_material(
                title,
                tags,
            )
        else:
            category = classify_plugin(
                title,
                tags,
            )

        items.append(
            {
                "title": title,
                "url": url,
                "category": category,
                "source": "RPG Maker Guild",
                "tags": tags,
            }
        )

    return items


def get_page(session, url, page):
    """
    Discourseカテゴリ一覧を取得する。

    page=1はカテゴリURLそのもの、
    2以降はDiscourseが提供する ?page=N を使用する。
    """

    if page == 1:
        page_url = url
    else:
        separator = "&" if "?" in url else "?"
        page_url = f"{url}{separator}page={page}"

    response = session.get(
        page_url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    return response.text


# ==========================================
# Main
# ==========================================

def get_items(seen):

    session = requests.Session()

    adopted_items = []
    new_seen = seen.copy()
    seen_set = set(seen)
    current_urls = set()

    try:

        targets = [
            (GUILD_URL, "material"),
            (GUILD_PLUGIN_URL, "plugin"),
        ]

        for category_url, category_type in targets:

            for page in range(
                1,
                MAX_PAGES + 1,
            ):

                try:
                    html = get_page(
                        session,
                        category_url,
                        page,
                    )

                except requests.RequestException as e:

                    print(
                        "[RPG Maker Guild] "
                        f"Page error: {e}"
                    )
                    break

                items = extract_topics(
                    html,
                    category_type,
                )

                if not items:
                    break

                for item in items:

                    url = item["url"]

                    if url in current_urls:
                        continue

                    current_urls.add(url)

                    if url in seen_set:
                        continue

                    adopted_items.append(item)
                    new_seen.append(url)
                    seen_set.add(url)

        print(
            "[RPG Maker Guild] New: "
            f"{len(adopted_items)}"
        )

        return (
            adopted_items,
            new_seen,
        )

    except requests.RequestException as e:

        print(
            "[RPG Maker Guild] Request Error: "
            f"{e}"
        )

        return [], seen

    except Exception as e:

        print(
            "[RPG Maker Guild] Error: "
            f"{e}"
        )

        return [], seen
