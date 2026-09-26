# ==========================================
# VisuStella
# ==========================================

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import (
    VISUSTELLA_URL,
    VISUSTELLA_SEEN_FILE,
)

from sources.base import get_html


SEEN_FILE = VISUSTELLA_SEEN_FILE


# ==========================================
# Plugin判定
# ==========================================

def normalize_visustella_url(url):
    """VisuStellaのURL表記を正規化する。"""

    if not isinstance(url, str):
        return None

    url = url.strip()

    if not url:
        return None

    url = url.split("#", 1)[0]
    url = url.split("?", 1)[0]
    url = url.rstrip("/")

    return url


def classify_visustella(title, url=""):

    normalized = title.lower().strip()

    # --------------------------------------
    # RPG Maker MZ Plugin
    # --------------------------------------

    if "plugin" in normalized:
        return "VisuStellaプラグイン"

    return None


# ==========================================
# Main
# ==========================================

def get_items(seen):

    try:

        html = get_html(
            VISUSTELLA_URL
        )

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        adopted_items = []

        new_seen = seen.copy()

        seen_urls = set()

        # ----------------------------------
        # itch.ioの商品カード
        # ----------------------------------

        game_cells = soup.select(
            ".game_cell"
        )

        for cell in game_cells:

            link = cell.select_one(
                "a[href]"
            )

            if not link:
                continue

            href = link.get(
                "href"
            )

            if not href:
                continue

            href = urljoin(
                VISUSTELLA_URL,
                href,
            )
            href = normalize_visustella_url(href)

            if not href:
                continue

            # VisuStella以外へのリンクを除外
            if "visustellamz.itch.io/" not in href:
                continue

            # トップページ自身を除外
            if (
                href
                == VISUSTELLA_URL.rstrip("/")
            ):
                continue

            # 重複除外
            if href in seen_urls:
                continue

            seen_urls.add(href)

            # 既取得
            if href in seen:
                continue

            # --------------------------------
            # タイトル
            # --------------------------------

            title_tag = cell.select_one(
                ".game_title"
            )

            if title_tag:

                title = title_tag.get_text(
                    " ",
                    strip=True,
                )

            else:

                title = link.get_text(
                    " ",
                    strip=True,
                )

            if not title:
                continue

            # --------------------------------
            # 分類
            # --------------------------------

            category = classify_visustella(
                title,
                href,
            )

            if category is None:
                continue

            # --------------------------------
            # 採用
            # --------------------------------

            new_seen.append(
                href
            )

            adopted_items.append(
                {
                    "title": title,
                    "url": href,
                    "category": category,
                    "source": "VisuStella",
                }
            )

        print(
            f"[VisuStella] New: "
            f"{len(adopted_items)}"
        )

        return (
            adopted_items,
            new_seen,
        )

    except Exception as e:

        print(
            f"[VisuStella] Error: {e}"
        )

        return [], seen
