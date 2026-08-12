# ==========================================
# DeviantArt
# ==========================================

from urllib.parse import (
    quote_plus,
    urljoin,
)

from bs4 import BeautifulSoup

from config import (
    DEVIANTART_SEARCHES,
    DEVIANTART_SEEN_FILE,
)

from categories.assets import (
    classify_asset,
)

from sources.base import get_html


SEEN_FILE = DEVIANTART_SEEN_FILE

DEVIANTART_BASE_URL = (
    "https://www.deviantart.com/"
)

DEVIANTART_SEARCH_URL = (
    "https://www.deviantart.com/search?q="
)


# ==========================================
# URL判定
# ==========================================

def is_deviation_url(url):

    return (
        "deviantart.com/" in url
        and "/art/" in url
    )


# ==========================================
# 検索URL
# ==========================================

def build_search_url(query):

    return (
        DEVIANTART_SEARCH_URL
        + quote_plus(query)
    )


# ==========================================
# Main
# ==========================================

def get_items(seen):

    try:

        adopted_items = []

        new_seen = seen.copy()

        seen_urls = set()

        # ----------------------------------
        # 複数検索
        # ----------------------------------

        for query in DEVIANTART_SEARCHES:

            search_url = build_search_url(
                query
            )

            print(
                f"[DeviantArt] Search: {query}"
            )

            html = get_html(
                search_url
            )

            print(
                f"[DeviantArt] HTML length: "
                f"{len(html)}"
            )

            soup = BeautifulSoup(
                html,
                "html.parser",
            )

            # ----------------------------------
            # 投稿リンク
            # ----------------------------------

            links = soup.select(
                'a[href*="/art/"]'
            )

            print(
                f"[DeviantArt] "
                f"Candidate links: {len(links)}"
            )

            for link in links:

                href = link.get(
                    "href"
                )

                if not href:
                    continue

                href = urljoin(
                    DEVIANTART_BASE_URL,
                    href,
                )

                # --------------------------------
                # DeviantArtの作品ページだけ
                # --------------------------------

                if not is_deviation_url(
                    href
                ):
                    continue

                # --------------------------------
                # トラッキングパラメータ除去
                # --------------------------------

                href = href.split(
                    "?",
                    1
                )[0]

                # --------------------------------
                # 同一実行内の重複
                # --------------------------------

                if href in seen_urls:
                    continue

                seen_urls.add(
                    href
                )

                # --------------------------------
                # 過去取得
                # --------------------------------

                if href in seen:
                    continue

                # --------------------------------
                # タイトル
                # --------------------------------

                title = link.get_text(
                    " ",
                    strip=True,
                )

                if not title:
                    continue

                # --------------------------------
                # 異常に長いリンク文字列
                # --------------------------------

                if len(title) > 300:
                    continue

                # --------------------------------
                # 素材分類
                # --------------------------------

                result = classify_asset(
                    title,
                    href,
                )

                if isinstance(
                    result,
                    tuple,
                ):

                    category = result[0]
                    tags = result[1]

                else:

                    category = result
                    tags = []

                # --------------------------------
                # 素材でなければ除外
                # --------------------------------

                if category is None:
                    continue

                # --------------------------------
                # 採用
                # --------------------------------

                item = {
                    "title": title,
                    "url": href,
                    "category": category,
                    "source": "DeviantArt",
                }

                if tags:
                    item["tags"] = tags

                adopted_items.append(
                    item
                )

                new_seen.append(
                    href
                )

                print(
                    f"[DeviantArt]"
                    f"[{category}] "
                    f"{title}"
                )

        print(
            f"[DeviantArt] New: "
            f"{len(adopted_items)}"
        )

        return (
            adopted_items,
            new_seen,
        )

    except Exception as e:

        print(
            f"[DeviantArt] Error: {e}"
        )

        return [], seen
