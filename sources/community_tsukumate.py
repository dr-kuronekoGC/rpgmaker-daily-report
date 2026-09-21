# ==========================================
# ツクマテ
# ==========================================

from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup

from config import (
    TSUKUMATE_URL,
    TSUKUMATE_SEEN_FILE,
    REQUEST_TIMEOUT,
    USER_AGENT,
)
from sources.base import get_html


SEEN_FILE = TSUKUMATE_SEEN_FILE

SOURCE_NAME = "ツクマテ"
BASE_URL = "https://tm.yumineko.com/"

# RPGツクールMZの親フォーラム。
MZ_FORUM_URL = TSUKUMATE_URL

# 1回の実行で見るページ数。
MAX_PAGES = 2

# phpBBの「素材投稿・プラグイン・TIPS」のうち、
# Daily Reportで収集対象とするフォーラム名。
ADOPTED_FORUMS = {
    "MZ:素材の投稿・ダウンロード": "ツクマテグラフィック素材",
    "MZ：プラグイン素材": "ツクマテプラグイン",
    "MZ：小ネタ・TIPS・講座": "ツクマテTips",
}

# 音声系はMZ専用フォーラムではなく「音楽・人員募集」にまとまっているため、
# 現段階では無理に全体監視せず、MZ系を優先する。
# 将来必要なら音声素材フォーラムを別ソースとして追加する。


def normalize_url(url):
    if not isinstance(url, str):
        return None

    url = url.strip()

    if not url:
        return None

    url = urljoin(BASE_URL, url)

    parsed = urlparse(url)

    # sidなどのセッション情報は除去する。
    params = parse_qs(parsed.query)

    if "viewtopic.php" in parsed.path:
        allowed = {
            key: values
            for key, values in params.items()
            if key in {"t", "f", "start"}
        }
    elif "viewforum.php" in parsed.path:
        allowed = {
            key: values
            for key, values in params.items()
            if key in {"f", "start"}
        }
    else:
        allowed = params

    query_parts = []
    for key, values in allowed.items():
        for value in values:
            query_parts.append(
                f"{key}={value}"
            )

    query = "&".join(query_parts)

    if query:
        return (
            f"{parsed.scheme}://{parsed.netloc}"
            f"{parsed.path}?{query}"
        )

    return (
        f"{parsed.scheme}://{parsed.netloc}"
        f"{parsed.path}"
    )


def get_mz_forums():
    """
    RPGツクールMZ親フォーラムから、対象サブフォーラムを取得する。

    固定IDを大量にハードコードせず、トップ側のリンクを基準にする。
    """
    html = get_html(
        MZ_FORUM_URL
    )

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    forums = {}

    for link in soup.select(
        "a[href*='viewforum.php?f=']"
    ):
        name = link.get_text(
            " ",
            strip=True,
        )

        if name not in ADOPTED_FORUMS:
            continue

        url = normalize_url(
            link.get("href")
        )

        if not url:
            continue

        forums[name] = url

    return forums


def extract_topics(
    html,
    forum_name,
):
    """
    phpBBのトピック一覧からトップレベルのトピックを抽出する。
    """
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    topics = []
    seen_urls = set()

    for link in soup.select(
        "a.topictitle[href]"
    ):
        title = link.get_text(
            " ",
            strip=True,
        )

        raw_url = link.get(
            "href"
        )

        if not title or not raw_url:
            continue

        url = normalize_url(
            raw_url
        )

        if not url:
            continue

        # phpBBの同一ページには最新記事へのリンク等が
        # 複数存在するため、トピックURL単位で重複排除する。
        if url in seen_urls:
            continue

        # トピック以外のviewforumリンク等を除外。
        if "viewtopic.php" not in url:
            continue

        seen_urls.add(url)

        topics.append(
            {
                "title": title,
                "url": url,
                "forum_name": forum_name,
            }
        )

    return topics


def get_page_url(
    forum_url,
    page,
):
    if page <= 0:
        return forum_url

    separator = (
        "&"
        if "?" in forum_url
        else "?"
    )

    return (
        f"{forum_url}"
        f"{separator}"
        f"start={page * 25}"
    )


def classify_topic(
    forum_name,
    title,
):
    """
    掲示板のカテゴリを、そのままDaily Reportの分類へ変換する。

    質問・リクエストは収集対象外。
    """
    category = ADOPTED_FORUMS.get(
        forum_name
    )

    if category is None:
        return None

    normalized = title.lower().strip()

    question_keywords = (
        "質問",
        "教えて",
        "わからない",
        "分からない",
        "できますか",
        "方法",
        "how to",
        "help",
        "question",
        "request",
        "リクエスト",
    )

    if any(
        keyword.lower() in normalized
        for keyword in question_keywords
    ):
        # 「素材の投稿・ダウンロード」内でも
        # 質問・リクエスト系タイトルは除外する。
        return None

    if category == "ツクマテTips":
        return category

    return category


def get_items(seen):
    """
    ツクマテのMZ向け素材・プラグイン・Tipsを収集する。

    初回実行時は現在のトピックをベースラインとして記録し、
    過去記事を一気にSlackへ流さない。
    """
    try:
        forums = get_mz_forums()

        if not forums:
            print(
                f"[{SOURCE_NAME}] "
                "対象フォーラムを取得できませんでした。"
            )
            return [], seen

        # 初回は現在状態をベースライン化。
        if not seen:
            baseline = []

            for forum_name, forum_url in forums.items():
                html = get_html(
                    forum_url
                )

                topics = extract_topics(
                    html,
                    forum_name,
                )

                for topic in topics:
                    baseline.append(
                        topic["url"]
                    )

            print(
                f"[{SOURCE_NAME}] Baseline: "
                f"{len(baseline)} topics"
            )

            return [], baseline

        seen_set = set(seen)
        new_seen = list(seen)
        adopted_items = []

        for forum_name, forum_url in forums.items():
            for page in range(
                MAX_PAGES
            ):
                page_url = get_page_url(
                    forum_url,
                    page,
                )

                html = get_html(
                    page_url
                )

                topics = extract_topics(
                    html,
                    forum_name,
                )

                if not topics:
                    break

                for topic in topics:
                    url = topic["url"]

                    if url in seen_set:
                        continue

                    # 新規トピックとしては記録する。
                    # 採用対象外でも、同じ質問を毎回拾わない。
                    new_seen.append(url)
                    seen_set.add(url)

                    category = classify_topic(
                        forum_name,
                        topic["title"],
                    )

                    if category is None:
                        print(
                            f"[{SOURCE_NAME}] Skip: "
                            f"{topic['title']}"
                        )
                        continue

                    adopted_items.append(
                        {
                            "title": topic["title"],
                            "url": url,
                            "category": category,
                            "source": SOURCE_NAME,
                        }
                    )

                    print(
                        f"[{SOURCE_NAME}]"
                        f"[{category}] "
                        f"{topic['title']}"
                    )

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
