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

# トピック詳細を取得するときの待機時間
TOPIC_REQUEST_INTERVAL = 0.5

# Guildカテゴリ一覧を取得した後の待機時間
CATEGORY_REQUEST_INTERVAL = 1.0

# Guildの対象カテゴリ
#
# ここでは「収集候補」を拾うために使用する。
# 最終的な分類はトピック自身のcategory_idを優先する。
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

def extract_categories_from_json(data):
    """
    Discourseのcategories.jsonから、

        category_id -> category_name

    の辞書を作る。

    Discourseのレスポンス形式の違いに備えて、
    category_list.categories を基本としつつ、
    categories 直下も扱う。
    """

    categories = []

    if not isinstance(data, dict):
        return categories

    category_list = data.get("category_list")

    if isinstance(category_list, dict):
        values = category_list.get("categories")

        if isinstance(values, list):
            categories.extend(values)

    values = data.get("categories")

    if isinstance(values, list):
        categories.extend(values)

    return categories


def build_category_map(data):
    """
    category_id -> category_name

    親カテゴリ・サブカテゴリの両方を扱う。
    """

    category_map = {}

    categories = extract_categories_from_json(data)

    for category in categories:

        if not isinstance(category, dict):
            continue

        category_id = category.get("id")
        name = category.get("name")

        if category_id is not None and name:
            category_map[int(category_id)] = (
                str(name).strip()
            )

        # Discourseのcategory JSONに
        # subcategory_list等が含まれる場合に備える。
        children = category.get(
            "subcategory_list"
        )

        if isinstance(children, dict):
            children = children.get(
                "subcategories",
                []
            )

        if not isinstance(children, list):
            children = []

        for child in children:

            if not isinstance(child, dict):
                continue

            child_id = child.get("id")
            child_name = child.get("name")

            if (
                child_id is not None
                and child_name
            ):
                category_map[int(child_id)] = (
                    str(child_name).strip()
                )

    return category_map


def get_category_map(session):
    """
    Guild全体のカテゴリ一覧を取得し、
    category_id -> category_name を作る。

    取得できなかった場合は空辞書を返す。
    この場合、カテゴリを推測して採用しない。
    """

    try:

        data = get_json(
            session,
            CATEGORIES_JSON_URL,
        )

        category_map = build_category_map(data)

        print(
            "[Guild] Category map: "
            f"{len(category_map)} categories"
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
    """
    一覧ページから取得できるタグを取得する。
    """

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
    """
    トピック自身のカテゴリが「素材」の場合に、
    グラフィック素材とサウンド素材へ分類する。

    サウンドと明確に判断できない場合は
    グラフィック素材とする。
    """

    text = " ".join(
        [title] + list(tags)
    ).lower()

    # ----------------------------------
    # 日本語キーワード
    # ----------------------------------

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

    # ----------------------------------
    # 英語キーワード
    # ----------------------------------

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
    """
    トピック自身のカテゴリが「素材」であっても、
    実際の内容が質問・ゲーム紹介などである可能性が
    あるため、二次的に内容を確認する。

    明確なケースだけを判定する。
    判断できない場合はNoneを返し、
    通常の素材分類へ進める。
    """

    text = " ".join(
        [title] + list(tags)
    ).strip()

    normalized_tags = {
        str(tag).strip().lower()
        for tag in tags
        if str(tag).strip()
    }

    # ----------------------------------
    # タグによる質問判定
    # ----------------------------------

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

    # ----------------------------------
    # タイトルによる明確な質問判定
    # ----------------------------------

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

    # ----------------------------------
    # 明確なゲーム紹介・公開
    # ----------------------------------

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
    """
    トピック自身に設定されている実際のGuildカテゴリを
    Daily Reportのカテゴリへ変換する。

    基本方針:

    1. トピック詳細の実カテゴリを最優先する
    2. 質問・ゲーム・プラグインなどは、そのカテゴリを採用
    3. 実カテゴリが「素材」の場合のみ、
       グラフィック／サウンドへ細分類
    4. 「素材」内でも明確な質問・ゲーム紹介は
       二次判定する
    5. 詳細カテゴリを取得できなかった場合は
       誤分類防止のため採用しない

    guild_categoryは一覧ページ上のカテゴリであり、
    最終分類の根拠にはしない。
    """

    category = (
        actual_category or ""
    ).strip()

    if category in {
        "質問",
        "バグ報告",
    }:
        return "質問"

    if category in {
        "完成ゲーム",
        "制作中ゲーム",
    }:
        return "ゲーム"

    if category in {
        "プラグイン",
        "RPG Makerプラグイン",
        "RGSSx",
    }:
        return "プラグイン"

    if category == "素材":

        content_category = (
            classify_material_content(
                title,
                tags,
            )
        )

        if content_category is not None:
            return content_category

        return classify_material(
            title,
            tags,
        )

    # 雑談・お知らせなど、現在のDaily Reportで
    # 採用対象として定義していないカテゴリはNone。
    return None


# ==========================================
# Topic Extraction
# ==========================================

def extract_topics(html, guild_category):
    """
    Guildカテゴリ一覧ページからトピックを抽出する。
    """

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
    """
    Discourseカテゴリ一覧のページを取得する。
    """

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
):
    """
    トピック詳細JSONから、

        actual_category
        tags

    を取得する。

    category_nameが直接入っていればそれを優先し、
    取得できない場合はcategory_idを
    categories.jsonのマップから解決する。

    どちらも取得できなければ
    actual_categoryは空文字列とする。

    重要:
    カテゴリを推測して補完しない。
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
        return "", []

    # ----------------------------------
    # Category
    # ----------------------------------

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

    # ----------------------------------
    # Tags
    # ----------------------------------

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
    """
    Guildから新規トピックを取得する。

    カテゴリが確認できないトピックは、
    誤分類防止のためseenへ追加しない。
    """

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
                1,
                MAX_PAGES + 1,
            ):

                try:

                    html = get_page(
                        session,
                        category_url,
                        page,
                    )

                    topics = extract_topics(
                        html,
                        guild_category,
                    )

                except (
                    requests.RequestException
                ) as e:

                    print(
                        "[Guild] Listing error: "
                        f"{guild_category} "
                        f"page={page}: {e}"
                    )

                    continue

                if not topics:
                    continue

                for topic in topics:

                    title = topic[
                        "title"
                    ]

                    url = topic[
                        "url"
                    ]

                    tags = topic.get(
                        "tags",
                        [],
                    )

                    # ----------------------------------
                    # Duplicate protection
                    # ----------------------------------

                    if url in processed_urls:
                        continue

                    processed_urls.add(url)

                    if url in seen:
                        continue

                    # ----------------------------------
                    # Topic detail
                    # ----------------------------------

                    try:

                        (
                            actual_category,
                            detail_tags,
                        ) = get_topic_detail(
                            session,
                            url,
                            category_map,
                        )

                    except (
                        requests.RequestException
                    ) as e:

                        print(
                            "[Guild] Detail error: "
                            f"{title}: {e}"
                        )

                        # 詳細を取得できなかった場合は
                        # seenへ追加しない。
                        continue

                    if detail_tags:
                        tags = detail_tags

                    print(
                        "[Guild] Detail: "
                        f"{title} => "
                        f"{actual_category or '(unknown)'}"
                    )

                    # ----------------------------------
                    # Classification
                    # ----------------------------------

                    category = (
                        classify_guild_category(
                            guild_category,
                            actual_category,
                            title,
                            tags,
                        )
                    )

                    if category is None:

                        print(
                            "[Guild] Skip: "
                            f"{title} "
                            "(category not adopted)"
                        )

                        # カテゴリが確認できない、
                        # または対象外カテゴリの場合は
                        # seenへ追加しない。
                        continue

                    # ----------------------------------
                    # Adopt
                    # ----------------------------------

                    adopted_items.append(
                        {
                            "title": title,
                            "url": url,
                            "category": category,
                            "source": "RPG Maker Guild",
                        }
                    )

                    new_seen.append(url)

                    print(
                        "[Guild] Adopt: "
                        f"[{category}] "
                        f"{title}"
                    )

                    time.sleep(
                        TOPIC_REQUEST_INTERVAL
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

        # 途中まで正常取得できたものは
        # 維持する。
        return (
            adopted_items,
            new_seen,
        )
