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

# 1回のActionで取得するページ数
MAX_PAGES = 3

# トピック詳細を取得するときの待機時間。
# Guildへの短時間の連続アクセスを避ける。
TOPIC_REQUEST_INTERVAL = 0.5

# Guildの対象カテゴリ
#
# 現在のGuildでは、これらが独立した
# サブカテゴリとして存在する。
CATEGORY_URLS = {
    "プラグイン": (
        "https://guild.rpgmakerofficial.com/"
        "c/14-category/17-category/17"
    ),
    "素材": (
        "https://guild.rpgmakerofficial.com/"
        "c/14-category/20-category/20"
    ),
    "RGSSx": (
        "https://guild.rpgmakerofficial.com/"
        "c/14-category/21-category/21"
    ),
}


# ==========================================
# Material Classification
# ==========================================

def classify_material(title, tags):
    """
    Guildの「素材」カテゴリを、
    Daily Reportの表示カテゴリへ分類する。

    サウンドと明確に判断できない場合は
    グラフィック素材とする。
    """

    text = " ".join(
        [title] + list(tags)
    ).lower()

    # 日本語キーワード
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
    # 「se」は単純な部分一致にしない。
    # sprites / scene などへの誤反応を防ぐ。
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


# ==========================================
# Actual Guild Category Classification
# ==========================================

def classify_guild_category(
    guild_category,
    actual_category,
    title,
    tags,
):
    """
    トピック自身に設定されている実際のGuildカテゴリを
    Daily Reportのカテゴリへ変換する。

    一覧ページの取得元カテゴリだけで判断せず、
    トピック詳細のカテゴリを優先する。
    """

    category = (actual_category or "").strip()

    # ----------------------------------
    # 質問系
    # ----------------------------------

    if category in {
        "質問",
        "バグ報告",
    }:
        return "質問"

    # ----------------------------------
    # ゲーム系
    # ----------------------------------

    if category in {
        "完成ゲーム",
        "制作中ゲーム",
    }:
        return "ゲーム"

    # ----------------------------------
    # プラグイン系
    # ----------------------------------

    if category in {
        "プラグイン",
        "RPG Makerプラグイン",
        "RGSSx",
    }:
        return "プラグイン"

    # ----------------------------------
    # 素材
    # ----------------------------------

    if category == "素材":
        return classify_material(
            title,
            tags,
        )

    # ----------------------------------
    # 詳細カテゴリを取得できなかった場合
    # ----------------------------------
    #
    # 一時的な取得失敗で従来の収集機能を
    # 全停止させないためのフォールバック。

    if not category:

        if guild_category == "プラグイン":
            return "プラグイン"

        if guild_category == "RGSSx":
            return "プラグイン"

        if guild_category == "素材":
            return classify_material(
                title,
                tags,
            )

    # 雑談・お知らせなど、今回の対象から外すカテゴリは
    # 採用しない。
    return None


# ==========================================
# Tag Extraction
# ==========================================

def get_tags(topic):
    """
    Discourseトピックのタグを取得する。
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


# ==========================================
# Topic Extraction
# ==========================================

def extract_topics(
    html,
    guild_category,
):
    """
    Guildのカテゴリ一覧から
    トピックを抽出する。

    カテゴリはHTMLから推測せず、
    呼び出し元から明示的に渡す。
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

        # DiscourseのトピックURLのみ
        if not re.search(
            r"/t/[^/]+/\d+",
            url,
        ):
            continue

        # ----------------------------------
        # Tags
        # ----------------------------------

        tags = get_tags(
            topic
        )

        # ----------------------------------
        # Item
        # ----------------------------------

        items.append(
            {
                "title": title,
                "url": url,
                "category": None,
                "source": "RPG Maker Guild",
                "tags": tags,
                "guild_category": guild_category,
            }
        )

    return items


# ==========================================
# Page Fetch
# ==========================================

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
# Topic Detail Fetch
# ==========================================

def get_topic_detail(
    session,
    url,
):
    """
    DiscourseのトピックJSONから、
    トピック自身のカテゴリとタグを取得する。

    トピックページのパンくずに表示されるカテゴリと
    同じ情報をJSONから取得する。
    """

    topic_json_url = (
        url.rstrip("/")
        + ".json"
    )

    response = session.get(
        topic_json_url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    actual_category = data.get(
        "category_name",
        "",
    )

    json_tags = data.get(
        "tags",
        [],
    )

    if not isinstance(
        json_tags,
        list,
    ):
        json_tags = []

    tags = []

    for tag in json_tags:

        text = str(tag).strip()

        if text and text not in tags:
            tags.append(text)

    return (
        str(actual_category).strip(),
        tags,
    )


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

        # ==================================
        # 対象カテゴリを順番に取得
        # ==================================

        for guild_category, category_url in (
            CATEGORY_URLS.items()
        ):

            print(
                "[RPG Maker Guild] "
                f"Category: {guild_category}"
            )

            category_new = 0

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
                        f"Page error "
                        f"({guild_category}, "
                        f"page {page}): {e}"
                    )

                    # 取得できなかったページは
                    # そこで終了する。
                    break

                items = extract_topics(
                    html,
                    guild_category,
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

                    # ----------------------------------
                    # トピック自身のカテゴリを確認
                    # ----------------------------------
                    #
                    # 一覧ページのカテゴリだけでは、
                    # 「素材」一覧に質問・完成ゲームなどが
                    # 混ざるケースを正しく判定できないため、
                    # 新規トピックについて詳細情報を確認する。

                    actual_category = ""
                    detail_tags = []

                    try:

                        (
                            actual_category,
                            detail_tags,
                        ) = get_topic_detail(
                            session,
                            url,
                        )

                        print(
                            "[RPG Maker Guild] "
                            f"Detail: "
                            f"{item['title']} "
                            f"=> "
                            f"{actual_category or '(unknown)'}"
                        )

                    except (
                        requests.RequestException,
                        ValueError,
                        TypeError,
                    ) as e:

                        print(
                            "[RPG Maker Guild] "
                            "Detail error: "
                            f"{item['title']} - {e}"
                        )

                    # JSON側のタグを優先
                    if detail_tags:
                        item["tags"] = detail_tags

                    category = classify_guild_category(
                        guild_category,
                        actual_category,
                        item["title"],
                        item.get("tags", []),
                    )

                    # ----------------------------------
                    # 対象外カテゴリ
                    # ----------------------------------

                    if category is None:

                        print(
                            "[RPG Maker Guild] "
                            "Skip category: "
                            f"{item['title']} "
                            f"({actual_category or guild_category})"
                        )

                        # 対象外カテゴリはseenに追加しない。
                        #
                        # 後からカテゴリ変更された場合に
                        # 再取得できるようにする。
                        continue

                    # ----------------------------------
                    # 採用
                    # ----------------------------------

                    item["category"] = category

                    adopted_items.append(
                        item
                    )

                    new_seen.append(
                        url
                    )

                    seen_set.add(
                        url
                    )

                    category_new += 1

                    # トピック詳細取得の間隔
                    time.sleep(
                        TOPIC_REQUEST_INTERVAL
                    )

                # ページ間隔
                if page < MAX_PAGES:
                    time.sleep(1.0)

            print(
                "[RPG Maker Guild] "
                f"{guild_category} New: "
                f"{category_new}"
            )

            # カテゴリ間隔
            time.sleep(1.0)

        # ==================================
        # Result
        # ==================================

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
