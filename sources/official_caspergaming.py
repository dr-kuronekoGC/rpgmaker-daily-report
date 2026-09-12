# ==========================================
# Casper Gaming
# ==========================================

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import (
    CASPER_RESOURCES_URL,
    CASPER_SOUND_URL,
    CASPER_MAP_URL,
    CASPER_PLUGINS_URL,
    CASPER_SEEN_FILE,
    REQUEST_TIMEOUT,
    USER_AGENT,
)

import requests


SEEN_FILE = CASPER_SEEN_FILE


HEADERS = {
    "User-Agent": USER_AGENT,
}


# ==========================================
# 対象ページ
# ==========================================

SOURCE_PAGES = [
    (
        CASPER_PLUGINS_URL,
        "プラグイン",
    ),
    (
        CASPER_RESOURCES_URL,
        "グラフィック素材",
    ),
    (
        CASPER_SOUND_URL,
        "サウンド素材",
    ),
    (
        CASPER_MAP_URL,
        "グラフィック素材",
    ),
]


# ==========================================
# URL分類
# ==========================================

def classify_url(url):
    """
    Casper Gamingの詳細ページURLから
    Daily Report用カテゴリを決定する。
    """

    normalized = url.lower()

    # --------------------------------------
    # Plugins
    # --------------------------------------

    if "/plugins/" in normalized:
        return "プラグイン"

    # --------------------------------------
    # Audio / Sound
    # --------------------------------------

    # 現在のCasper Gamingでは
    # /resources/mz/sound/ が使用されている。
    if "/resources/mz/sound/" in normalized:
        return "サウンド素材"

    # 旧構造にも対応
    if "/resources/mz/audio/" in normalized:
        return "サウンド素材"

    # --------------------------------------
    # Graphics
    # --------------------------------------

    if "/resources/mz/graphics/" in normalized:
        return "グラフィック素材"

    # --------------------------------------
    # Maps
    # --------------------------------------

    # 現在のCasper Gamingでは
    # /resources/mz/maps/ が使用されている。
    if "/resources/mz/maps/" in normalized:
        return "グラフィック素材"

    # 旧構造にも対応
    if "/resources/mz/map/" in normalized:
        return "グラフィック素材"

    return None


# ==========================================
# URL判定
# ==========================================

def is_target_url(url):
    """
    Casper Gamingの個別リソースページだけを
    対象にする。
    """

    if not url:
        return False

    normalized = url.lower()

    patterns = [
        # Plugins
        r"/plugins/cgmz/[^/]+/?$",

        # Graphics
        r"/resources/mz/graphics/[^/]+/?$",

        # Sound
        r"/resources/mz/sound/[^/]+/?$",
        r"/resources/mz/audio/[^/]+/?$",

        # Maps
        r"/resources/mz/maps/[^/]+/?$",
        r"/resources/mz/map/[^/]+/?$",
    ]

    return any(
        re.search(pattern, normalized)
        for pattern in patterns
    )


# ==========================================
# タイトル候補
# ==========================================

IGNORE_TITLES = {
    "image info",
    "sound info",
    "map info",
    "download graphic",
    "download sound",
    "download map pack",
    "get pack",
    "get plugin",
    "forum",
    "itch",
    "view on itch",
    "view itch page",
    "access",
    "preview",
    "buy",
}


def clean_title(text):
    """
    リンク文字列からタイトルとして
    不適切なものを除外する。
    """

    if not text:
        return None

    title = " ".join(
        text.split()
    ).strip()

    if not title:
        return None

    if title.lower() in IGNORE_TITLES:
        return None

    return title


# ==========================================
# HTML取得
# ==========================================

def get_html(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    return response.text


# ==========================================
# ページ解析
# ==========================================

def extract_items(
    html,
    source_url,
    fallback_category,
    seen_urls,
):
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    items = []

    # --------------------------------------
    # ページ内のリンクを確認
    # --------------------------------------

    for link in soup.select(
        "a[href]"
    ):

        href = link.get(
            "href"
        )

        if not href:
            continue

        url = urljoin(
            source_url,
            href,
        )

        # ----------------------------------
        # 対象URLのみ
        # ----------------------------------

        if not is_target_url(
            url
        ):
            continue

        # ----------------------------------
        # 重複
        # ----------------------------------

        if url in seen_urls:
            continue

        seen_urls.add(url)

        # ----------------------------------
        # カテゴリ
        # ----------------------------------

        category = classify_url(
            url
        )

        if category is None:
            category = fallback_category

        # ----------------------------------
        # タイトル
        # ----------------------------------

        title = clean_title(
            link.get_text(
                " ",
                strip=True,
            )
        )

        if not title:
            continue

        # ----------------------------------
        # 明らかにボタン系のリンクを除外
        # ----------------------------------

        lower_title = title.lower()

        if lower_title in IGNORE_TITLES:
            continue

        # ----------------------------------
        # 採用
        # ----------------------------------

        items.append(
            {
                "title": title,
                "url": url,
                "category": category,
                "source": "Casper Gaming",
            }
        )

    return items


# ==========================================
# Main
# ==========================================

def get_items(seen):

    adopted_items = []

    new_seen = seen.copy()

    seen_urls = set()

    try:

        for source_url, fallback_category in SOURCE_PAGES:

            try:

                print(
                    f"[Casper Gaming] "
                    f"Category: {fallback_category}"
                )

                html = get_html(
                    source_url
                )

                page_items = extract_items(
                    html,
                    source_url,
                    fallback_category,
                    seen_urls,
                )

                page_new = 0

                for item in page_items:

                    url = item.get(
                        "url"
                    )

                    if not url:
                        continue

                    # --------------------------------
                    # 既取得
                    # --------------------------------

                    if url in seen:
                        continue

                    # --------------------------------
                    # 新規採用
                    # --------------------------------

                    new_seen.append(
                        url
                    )

                    adopted_items.append(
                        item
                    )

                    page_new += 1

                    print(
                        "[Casper Gaming]"
                        f"[{item['category']}] "
                        f"{item['title']}"
                    )

                print(
                    f"[Casper Gaming] "
                    f"{fallback_category} New: "
                    f"{page_new}"
                )

            except Exception as e:

                print(
                    "[Casper Gaming] "
                    f"Page Error: "
                    f"{source_url} | {e}"
                )

        # --------------------------------------
        # 結果
        # --------------------------------------

        categories = {}

        for item in adopted_items:

            category = item.get(
                "category"
            )

            categories[category] = (
                categories.get(
                    category,
                    0,
                )
                + 1
            )

        print(
            "[Casper Gaming] New: "
            f"{len(adopted_items)}"
        )

        print(
            "[Casper Gaming] Categories: "
            f"{categories}"
        )

        return (
            adopted_items,
            new_seen,
        )

    except Exception as e:

        print(
            f"[Casper Gaming] Error: {e}"
        )

        return (
            [],
            seen,
        )
