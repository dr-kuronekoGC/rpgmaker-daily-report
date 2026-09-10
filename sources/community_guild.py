# ==========================================
# RPG Maker Guild
# ==========================================

import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import (
    GUILD_URL,
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

# 1回のActionで取得するページ数。
MAX_PAGES = 3


# GuildからDaily Reportへ採用するカテゴリ。
#
# 「RPG Makerプラグイン」は実際のGuild上で
# 使用されている正式カテゴリ名。
TARGET_CATEGORIES = {
    "素材",
    "プラグイン",
    "RPG Makerプラグイン",
    "RGSSx",
}


# ==========================================
# Category Classification
# ==========================================

def classify_material(title, tags):
    """
    Guildの「素材」カテゴリを、
    Daily Reportの表示カテゴリへ分類する。

    Guild側に「グラフィック」「サウンド」の
    細分類がないため、タイトルとタグから判定する。

    判定できないものは「グラフィック素材」とする。
    """

    text = " ".join(
        [title] + list(tags)
    ).lower()

    # 日本語の明確なキーワード
    japanese_sound_keywords = [
        "bgm",
        "bgs",
        "音楽",
        "効果音",
        "サウンド",
        "音声",
        "se素材",
        "bgm素材",
        "音素材",
    ]

    for keyword in japanese_sound_keywords:

        if keyword in text:
            return "サウンド素材"

    # 英語キーワード
    #
    # 「se」は単純な部分一致にすると
    # sprites / scene などに誤反応するため使用しない。
    english_sound_patterns = [
        r"\bbgm\b",
        r"\bbgs\b",
        r"\baudio\b",
        r"\bmusic\b",
        r"\bsfx\b",
        r"\bsound\b",
        r"\bsound effect\b",
        r"\bsound effects\b",
    ]

    for pattern in english_sound_patterns:

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            return "サウンド素材"

    return "グラフィック素材"


def classify_category(
    guild_category,
    title,
    tags,
):
    """
    Guildの正式カテゴリを
    Daily Reportのカテゴリへ変換する。

    Guild側のカテゴリを信頼し、
    タイトルからカテゴリを推測しない。
    """

    if guild_category in {
        "プラグイン",
        "RPG Makerプラグイン",
        "RGSSx",
    }:
        return "プラグイン"

    if guild_category == "素材":
        return classify_material(
            title,
            tags,
        )

    return None


# ==========================================
# Helpers
# ==========================================

def get_topic_category(topic):
    """
    トピック一覧からGuild側のカテゴリ名を取得する。
    """

    category_name = topic.select_one(
        ".badge-category .category-name"
    )

    if category_name is not None:

        text = category_name.get_text(
            " ",
            strip=True,
        )

        if text:
            return text

    # 念のため別形式にも対応
    category_name = topic.select_one(
        ".category-name"
    )

    if category_name is not None:

        text = category_name.get_text(
            " ",
            strip=True,
        )

        if text:
            return text

    return ""


def get_tags(topic):
    """
    Discourseトピックに付与されたタグを取得する。
    """

    tags = []

    for tag in topic.select(
        ".discourse-tag"
    ):

        text = tag.get_text(
            " ",
            strip=True,
        )

        if not text:
            continue

        if text not in tags:
            tags.append(text)

    return tags


def extract_topics(html):
    """
    Guildのカテゴリ一覧からトピックを抽出する。
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

        # ----------------------------------
        # Title / URL
        # ----------------------------------

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

        # DiscourseのトピックURLだけを対象にする。
        if not re.search(
            r"/t/[^/]+/\d+",
            url,
        ):
            continue

        # ----------------------------------
        # Guild category
        # ----------------------------------

        guild_category = get_topic_category(
            topic
        )

        # 対象外カテゴリはここで除外。
        if guild_category not in TARGET_CATEGORIES:
            continue

        # ----------------------------------
        # Tags
        # ----------------------------------

        tags = get_tags(
            topic
        )

        # ----------------------------------
        # Daily Report category
        # ----------------------------------

        category = classify_category(
            guild_category,
            title,
            tags,
        )

        if category is None:
            continue

        # ----------------------------------
        # Item
        # ----------------------------------

        items.append(
            {
                "title": title,
                "url": url,
                "category": category,
                "source": "RPG Maker Guild",
                "tags": tags,
                "guild_category": guild_category,
            }
        )

    return items


def get_page(
    session,
    url,
    page,
):
    """
    Discourseカテゴリ一覧を取得する。

    page=1はカテゴリURLそのもの。
    2以降は ?page=N を使用する。
    """

    if page == 1:

        page_url = url

    else:

        separator = (
            "&"
            if "?" in url
            else "?"
        )

        page_url = (
            f"{url}"
            f"{separator}"
            f"page={page}"
        )

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

    seen_set = set(
        seen
    )

    current_urls = set()

    try:

        # ----------------------------------
        # Guildのメインカテゴリだけを見る
        # ----------------------------------

        for page in range(
            1,
            MAX_PAGES + 1,
        ):

            try:

                html = get_page(
                    session,
                    GUILD_URL,
                    page,
                )

            except requests.RequestException as e:

                print(
                    "[RPG Maker Guild] "
                    f"Page error: {e}"
                )

                break

            items = extract_topics(
                html
            )

            for item in items:

                url = item[
                    "url"
                ]

                # 同一Action内の重複防止
                if url in current_urls:
                    continue

                current_urls.add(
                    url
                )

                # 過去に取得済みならスキップ
                if url in seen_set:
                    continue

                adopted_items.append(
                    item
                )

                new_seen.append(
                    url
                )

                seen_set.add(
                    url
                )

            # ページ間に少し間隔を置く。
            # Guildへの過剰アクセスを避ける。
            if page < MAX_PAGES:
                time.sleep(1.0)

        # ----------------------------------
        # Result
        # ----------------------------------

        print(
            "[RPG Maker Guild] New: "
            f"{len(adopted_items)}"
        )

        category_counts = {}

        for item in adopted_items:

            category = item.get(
                "category",
                "unknown",
            )

            category_counts[
                category
            ] = (
                category_counts.get(
                    category,
                    0,
                )
                + 1
            )

        if category_counts:

            print(
                "[RPG Maker Guild] "
                "Categories: "
                f"{category_counts}"
            )

        return (
            adopted_items,
            new_seen,
        )

    except requests.RequestException as e:

        print(
            "[RPG Maker Guild] "
            f"Request Error: {e}"
        )

        return [], seen

    except Exception as e:

        print(
            "[RPG Maker Guild] "
            f"Error: {e}"
        )

        return [], seen
