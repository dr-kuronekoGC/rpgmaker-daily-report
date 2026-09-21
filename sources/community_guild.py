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

MAX_PAGES = 3

TOPIC_REQUEST_INTERVAL = 0.5

CATEGORY_REQUEST_INTERVAL = 1.0

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

CATEGORIES_JSON_URL = (
    "https://guild.rpgmakerofficial.com/"
    "categories.json"
    "?include_subcategories=true"
)


# ==========================================
# HTTP
# ==========================================

def get_json(session, url):
    response = session.get(
        url,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def get_html(session, url):
    response = session.get(
        url,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.text


# ==========================================
# Category Map
# ==========================================


def get_category_topics_json(session, category_url, page):
    """DiscourseのカテゴリJSONからトピック一覧を取得する。"""
    json_url = category_url.rstrip("/") + ".json"
    return get_json(
        session,
        json_url + "?page=" + str(page),
    )


def extract_topics_json(data, guild_category):
    """カテゴリJSONのtopic_listからトピックを抽出する。"""
    if not isinstance(data, dict):
        return []

    topic_list = data.get("topic_list")
    if not isinstance(topic_list, dict):
        return []

    raw_topics = topic_list.get("topics", [])
    if not isinstance(raw_topics, list):
        return []

    topics = []

    for topic in raw_topics:
        if not isinstance(topic, dict):
            continue

        topic_id = topic.get("id")
        title = str(topic.get("title") or "").strip()
        slug = str(topic.get("slug") or "topic").strip()

        if topic_id is None or not title:
            continue

        try:
            topic_id = int(topic_id)
        except (TypeError, ValueError):
            continue

        url = urljoin(
            GUILD_URL,
            f"/t/{slug}/{topic_id}",
        )

        tags = topic.get("tags", [])
        if not isinstance(tags, list):
            tags = []

        topics.append({
            "title": title,
            "url": url,
            "guild_category": guild_category,
            "tags": [
                str(tag).strip()
                for tag in tags
                if str(tag).strip()
            ],
        })

    return topics

def extract_categories_from_json(data):
    """
    Discourseのcategories.jsonから、
    カテゴリ候補を抽出する。

    診断のため、実際のJSON構造もログに出す。
    """

    categories = []

    if not isinstance(data, dict):
        print(
            "[Guild DEBUG] categories.json "
            "top-level is not dict: "
            f"{type(data).__name__}"
        )
        return categories

    print(
        "[Guild DEBUG] categories.json "
        f"top-level keys: {list(data.keys())}"
    )

    category_list = data.get(
        "category_list"
    )

    if isinstance(category_list, dict):

        print(
            "[Guild DEBUG] category_list keys: "
            f"{list(category_list.keys())}"
        )

        values = category_list.get(
            "categories"
        )

        if isinstance(values, list):

            print(
                "[Guild DEBUG] "
                "category_list.categories: "
                f"{len(values)} entries"
            )

            categories.extend(values)

            if values:
                print(
                    "[Guild DEBUG] "
                    "first category sample: "
                    f"{values[0]}"
                )

    values = data.get(
        "categories"
    )

    if isinstance(values, list):

        print(
            "[Guild DEBUG] top-level "
            f"categories: {len(values)} entries"
        )

        categories.extend(values)

        if values:
            print(
                "[Guild DEBUG] "
                "first top-level category sample: "
                f"{values[0]}"
            )

    return categories


def build_category_map(data):
    """
    category_id -> category_name

    親カテゴリ・サブカテゴリの両方を扱う。
    """

    category_map = {}

    categories = extract_categories_from_json(
        data
    )

    print(
        "[Guild DEBUG] "
        f"raw category entries: {len(categories)}"
    )

    for category in categories:

        if not isinstance(category, dict):
            continue

        category_id = category.get("id")
        name = category.get("name")

        if (
            category_id is not None
            and name
        ):
            try:
                normalized_id = int(
                    category_id
                )

                category_map[
                    normalized_id
                ] = str(name).strip()

            except (
                TypeError,
                ValueError,
            ):
                print(
                    "[Guild DEBUG] Invalid "
                    f"category id: {category_id!r}"
                )

        children = category.get(
            "subcategory_list"
        )

        if isinstance(children, dict):

            print(
                "[Guild DEBUG] "
                f"subcategory_list for "
                f"{name!r}: "
                f"keys={list(children.keys())}"
            )

            children = children.get(
                "subcategories",
                []
            )

        if not isinstance(
            children,
            list,
        ):
            children = []

        for child in children:

            if not isinstance(
                child,
                dict,
            ):
                continue

            child_id = child.get("id")
            child_name = child.get("name")

            if (
                child_id is not None
                and child_name
            ):
                try:
                    normalized_child_id = int(
                        child_id
                    )

                    category_map[
                        normalized_child_id
                    ] = str(
                        child_name
                    ).strip()

                except (
                    TypeError,
                    ValueError,
                ):
                    print(
                        "[Guild DEBUG] Invalid "
                        f"subcategory id: "
                        f"{child_id!r}"
                    )

    return category_map


def get_category_map(session):
    """
    Guild全体のカテゴリ一覧を取得し、
    category_id -> category_name を作る。

    取得できなかった場合は空辞書を返す。
    """

    try:

        data = get_json(
            session,
            CATEGORIES_JSON_URL,
        )

        category_map = build_category_map(
            data
        )

        print(
            "[Guild] Category map: "
            f"{len(category_map)} categories"
        )

        # 診断用。
        # 本番動作には影響しない。
        if category_map:

            print(
                "[Guild DEBUG] "
                "category_map contents:"
            )

            for (
                category_id,
                category_name,
            ) in sorted(
                category_map.items()
            ):

                print(
                    "  "
                    f"{category_id}: "
                    f"{category_name}"
                )

        return category_map

    except Exception as e:

        print(
            "[Guild] Category map error: "
            f"{e}"
        )

        return {}


# ==========================================
# Tags
# ==========================================

def get_tags(topic):

    tags = []

    for element in topic.select(
        ".discourse-tag"
    ):

        text = element.get_text(
            " ",
            strip=True,
        )

        if text:
            tags.append(text)

    return tags


# ==========================================
# Material Classification
# ==========================================

def classify_material(title, tags):

    text = " ".join(
        [title] + list(tags)
    ).lower()

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
# Material Content Sieve
# ==========================================

def classify_material_content(title, tags):

    text = " ".join(
        [title] + list(tags)
    ).strip()

    normalized_tags = {
        str(tag).strip().lower()
        for tag in tags
        if str(tag).strip()
    }

    question_tags = {
        "質問",
        "question",
        "questions",
        "help",
        "support",
    }

    if normalized_tags & {
        tag.lower()
        for tag in question_tags
    }:
        return "質問"

    question_patterns = [
        r"[？?]$",
        r"どうすれば",
        r"どうしたら",
        r"できますか",
        r"できますでしょうか",
        r"でしょうか",
        r"教えて",
        r"教えてください",
        r"わからない",
        r"分からない",
        r"できない",
        r"うまくいかない",
        r"やり方",
        r"方法を教えて",
        r"方法はありますか",
        r"方法がわから",
        r"修正方法",
        r"直す方法",
        r"解決方法",
        r"対処方法",
        r"how\s+to\b",
        r"\bhow\s+do\s+i\b",
        r"\bhelp\b",
        r"\bquestion\b",
    ]

    for pattern in question_patterns:

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            return "質問"

    game_patterns = [
        r"完成ゲーム",
        r"制作中ゲーム",
        r"ゲーム公開",
        r"ゲーム紹介",
        r"ゲーム作品",
        r"ホラーゲーム",
        r"無料ゲーム",
        r"\bgame\b",
        r"\bdlc\b",
        r"\bsteam\b",
        r"\bitch\.io\b",
    ]

    for pattern in game_patterns:

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            return "ゲーム"

    return None


# ==========================================
# Actual Guild Category Classification
# ==========================================

def classify_guild_category(
    guild_category,
    actual_category,
    title,
    tags,
):

    category = (
        actual_category or ""
    ).strip()

    # 質問・相談・バグ報告は、どのカテゴリに投稿されても
    # Daily Reportの収集対象にはしない。
    content_category = classify_material_content(
        title,
        tags,
    )

    if content_category == "質問":
        return None

    if content_category == "ゲーム":
        return None

    if category in {
        "質問",
        "バグ報告",
        "完成ゲーム",
        "制作中ゲーム",
        "雑談",
        "お知らせ",
    }:
        return None

    if category in {
        "プラグイン",
        "RPG Makerプラグイン",
        "RGSSx",
    }:
        return "プラグイン"

    if category == "素材":
        # 素材カテゴリではタイトルから質問・ゲームを除外したうえで、
        # サウンド／グラフィックを判定する。
        return classify_material(
            title,
            tags,
        )

    return None


# ==========================================
# Topic Extraction
# ==========================================

def extract_topics(
    html,
    guild_category,
):

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    topics = []

    for topic in soup.select(
        "tr.topic-list-item"
    ):

        title_element = topic.select_one(
            "a.title"
        )

        if title_element is None:
            continue

        title = title_element.get_text(
            " ",
            strip=True,
        )

        href = title_element.get(
            "href"
        )

        if not title or not href:
            continue

        url = urljoin(
            GUILD_URL,
            href,
        )

        tags = get_tags(topic)

        topics.append(
            {
                "title": title,
                "url": url,
                "guild_category": (
                    guild_category
                ),
                "tags": tags,
            }
        )

    return topics


# ==========================================
# Page
# ==========================================

def get_page(
    session,
    url,
    page,
):

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

    return get_html(
        session,
        page_url,
    )


# ==========================================
# Topic Detail
# ==========================================

def get_topic_detail(
    session,
    url,
    category_map,
    debug=False,
):
    """
    トピック詳細JSONから、

        actual_category
        tags

    を取得する。

    今回は診断のため、
    topic JSONのカテゴリ関連情報を出力する。
    """

    json_url = (
        url.rstrip("/")
        + ".json"
    )

    response = session.get(
        json_url,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, dict):

        print(
            "[Guild DEBUG] Topic JSON "
            "is not dict: "
            f"{type(data).__name__}"
        )

        return "", []

    # ==================================
    # Diagnostic
    # ==================================

    if debug:

        print(
            "[Guild DEBUG] Topic JSON keys:"
        )

        print(
            list(data.keys())
        )

        print(
            "[Guild DEBUG] "
            f"category_id = "
            f"{data.get('category_id')!r}"
        )

        print(
            "[Guild DEBUG] "
            f"category_name = "
            f"{data.get('category_name')!r}"
        )

        print(
            "[Guild DEBUG] "
            f"category = "
            f"{data.get('category')!r}"
        )

        print(
            "[Guild DEBUG] "
            f"tags = "
            f"{data.get('tags')!r}"
        )

        if isinstance(
            data.get("category"),
            dict,
        ):

            print(
                "[Guild DEBUG] "
                "category object keys: "
                f"{list(data['category'].keys())}"
            )

    # ==================================
    # Category
    # ==================================

    actual_category = (
        data.get("category_name")
        or ""
    ).strip()

    category_id = data.get(
        "category_id"
    )

    if (
        not actual_category
        and category_id is not None
    ):

        try:
            category_id = int(
                category_id
            )

        except (
            TypeError,
            ValueError,
        ):

            category_id = None

    if (
        not actual_category
        and category_id is not None
    ):

        actual_category = (
            category_map.get(
                category_id,
                "",
            )
            or ""
        ).strip()

    # ==================================
    # Tags
    # ==================================

    tags = []

    json_tags = data.get(
        "tags",
        [],
    )

    if isinstance(
        json_tags,
        list,
    ):

        tags = [
            str(tag).strip()
            for tag in json_tags
            if str(tag).strip()
        ]

    return (
        actual_category,
        tags,
    )


# ==========================================
# Main
# ==========================================

def get_items(seen):

    adopted_items = []

    new_seen = seen.copy()

    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    # ----------------------------------
    # Category map
    # ----------------------------------

    category_map = get_category_map(
        session
    )

    if not category_map:

        print(
            "[Guild] WARNING: "
            "Category map is empty."
        )

    # ----------------------------------
    # Same-run duplicate prevention
    # ----------------------------------

    processed_urls = set()

    # 診断対象。
    # 最初の3件だけtopic JSONの構造を出す。
    debug_topic_count = 0
    DEBUG_TOPIC_LIMIT = 3

    try:

        for (
            guild_category,
            category_url,
        ) in CATEGORY_URLS.items():

            print(
                "[Guild] Category listing: "
                f"{guild_category}"
            )

            for page in range(
                0,
                MAX_PAGES,
            ):

                try:
                    data = get_category_topics_json(
                        session,
                        category_url,
                        page,
                    )

                    topics = extract_topics_json(
                        data,
                        guild_category,
                    )

                except requests.RequestException as e:
                    print(
                        "[Guild] Listing error: "
                        f"{guild_category} page={page}: {e}"
                    )
                    continue

                if not topics:
                    if page == 0:
                        print(
                            "[Guild] No topics: "
                            f"{guild_category}"
                        )
                    continue

                for topic in topics:

                    title = topic["title"]
                    url = topic["url"]
                    tags = topic.get("tags", [])

                    if url in processed_urls:
                        continue

                    processed_urls.add(url)

                    if url in seen:
                        continue

                    actual_category = guild_category

                    category = classify_guild_category(
                        guild_category,
                        actual_category,
                        title,
                        tags,
                    )

                    if category is None:
                        print(
                            "[Guild] Skip: "
                            f"{title} "
                            "(category not adopted)"
                        )
                        continue

                    adopted_items.append({
                        "title": title,
                        "url": url,
                        "category": category,
                        "source": "RPG Maker Guild",
                    })

                    new_seen.append(url)

                    print(
                        "[Guild] Adopt: "
                        f"[{category}] {title}"
                    )

                time.sleep(
                    CATEGORY_REQUEST_INTERVAL
                )



        print(
            "[Guild] New: "
            f"{len(adopted_items)}"
        )

        return (
            adopted_items,
            new_seen,
        )

    except Exception as e:

        print(
            "[Guild] Error: "
            f"{e}"
        )

        return (
            adopted_items,
            new_seen,
        )
