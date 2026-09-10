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

# Guildカテゴリ一覧を取得した後の待機時間
CATEGORY_REQUEST_INTERVAL = 1.0

# Guildの対象カテゴリ
#
# ここでは「収集候補」を拾うために使用する。
# 実際の分類はトピック詳細のカテゴリを優先する。
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
# Material Content Sieve
# ==========================================

def classify_material_content(title, tags):
    """
    トピック自身のカテゴリが「素材」であっても、
    実際の内容が質問・相談などである可能性があるため、
    二次的に内容を確認する。

    明確な質問表現がある場合のみ「質問」とする。
    判定できない場合はNoneを返し、
    通常の素材分類へ進める。
    """

    text = " ".join(
        [title] + list(tags)
    ).strip()

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

    normalized_tags = {
        str(tag).strip().lower()
        for tag in tags
        if str(tag).strip()
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
        r"方法",
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
    4. 「素材」内でも明確な質問は質問へ回す
    5. 詳細カテゴリを取得できなかった場合は
       誤分類防止のため採用しない
    """

    category = (
        actual_category or ""
    ).strip()

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

        # まず素材カテゴリ内に混在している
        # 明確な質問・相談を除外する。
        content_category = (
            classify_material_content(
                title,
                tags,
            )
        )

        if content_category is not None:
            return content_category

        # 質問でなければ、素材の種類を判定する。
        return classify_material(
            title,
            tags,
        )

    # ----------------------------------
    # 対象外カテゴリ
    # ----------------------------------

    # 雑談・お知らせなど、今回のDaily Reportの
    # 対象外カテゴリは採用しない。
    #
    # 「お知らせ」を将来対象にしたくなった場合は、
    # ここに明示的に追加する。

    return None


# ==========================================
# Tag Extraction
# ==========================================

def get_tags(topic):
    """
    Discourseトピック一覧からタグを取得する。
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

    ここでは分類を確定しない。
    guild_categoryは「どの一覧から拾ったか」を
    記録するために使用する。
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

    - トピック自身のカテゴリ
    - トピック自身のタグ

    を取得する。

    詳細取得に失敗した場合は例外をそのまま返し、
    呼び出し側で「分類不能」として扱う。
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

                    # ----------------------------------
                    # 同一Action内の重複防止
                    # ----------------------------------

                    if url in current_urls:
                        continue

                    current_urls.add(
                        url
                    )

                    # ----------------------------------
                    # 過去に取得済みならスキップ
                    # ----------------------------------

                    if url in seen_set:
                        continue

                    # ----------------------------------
                    # トピック詳細を確認
                    # ----------------------------------
                    #
                    # ここが今回の重要ポイント。
                    #
                    # 一覧ページのカテゴリではなく、
                    # トピック自身のカテゴリを確認する。
                    #
                    # 例えば「素材」一覧に
                    # 「質問」や「完成ゲーム」が
                    # 混ざっていても、
                    # トピック自身が「質問」なら
                    # 「質問」として扱う。

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

                        # ----------------------------------
                        # 詳細取得失敗時は採用しない
                        # ----------------------------------
                        #
                        # ここで一覧カテゴリを使って
                        # 「素材」「プラグイン」などと
                        # 推測すると、今回修正したかった
                        # 誤分類が再発する。
                        #
                        # またseenにも追加しない。
                        # 次回Actionで再試行する。

                        continue

                    # ----------------------------------
                    # JSON側のタグを優先
                    # ----------------------------------

                    if detail_tags:
                        item["tags"] = detail_tags

                    # ----------------------------------
                    # 実カテゴリから分類
                    # ----------------------------------

                    category = classify_guild_category(
                        guild_category,
                        actual_category,
                        item["title"],
                        item.get(
                            "tags",
                            [],
                        ),
                    )

                    # ----------------------------------
                    # 対象外カテゴリ
                    # ----------------------------------

                    if category is None:

                        print(
                            "[RPG Maker Guild] "
                            "Skip category: "
                            f"{item['title']} "
                            f"({actual_category})"
                        )

                        # 対象外カテゴリはseenに追加しない。
                        #
                        # 将来的にカテゴリ変更された場合に
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

                    print(
                        "[RPG Maker Guild] "
                        f"Adopt: "
                        f"{item['title']} "
                        f"=> {category}"
                    )

                    # トピック詳細取得の間隔
                    time.sleep(
                        TOPIC_REQUEST_INTERVAL
                    )

                # ----------------------------------
                # ページ間隔
                # ----------------------------------

                if page < MAX_PAGES:
                    time.sleep(
                        CATEGORY_REQUEST_INTERVAL
                    )

            print(
                "[RPG Maker Guild] "
                f"{guild_category} New: "
                f"{category_new}"
            )

            # カテゴリ間隔
            time.sleep(
                CATEGORY_REQUEST_INTERVAL
            )

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
            f"Error: {e}"
        )

        return (
            adopted_items,
            new_seen,
        )

    finally:

        session.close()
