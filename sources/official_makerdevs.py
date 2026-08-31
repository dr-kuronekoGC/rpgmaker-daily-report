# ==========================================
# Maker Devs
# ==========================================

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import (
    MAKER_DEVS_URL,
    MAKER_DEVS_SEEN_FILE,
)

from sources.base import get_html


SEEN_FILE = MAKER_DEVS_SEEN_FILE


# ==========================================
# Plugin分類
# ==========================================

def classify_makerdevs(title, url=""):

    normalized = title.lower().strip()

    # --------------------------------------
    # 基本的にMaker DevsはPlugin directory
    # --------------------------------------

    if normalized:
        return "RPG Makerプラグイン"

    return None


# ==========================================
# Main
# ==========================================

def get_items(seen):

    try:

        html = get_html(
            MAKER_DEVS_URL
        )

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        adopted_items = []

        new_seen = seen.copy()

        seen_urls = set()

        # ----------------------------------
        # 一覧ページ内のリンクを取得
        # ----------------------------------

        for link in soup.select(
            "a[href]"
        ):

            href = link.get(
                "href"
            )

            if not href:
                continue

            href = urljoin(
                MAKER_DEVS_URL,
                href,
            )

            # --------------------------------
            # Maker Devs内部リンクのみ
            # --------------------------------

            if "makerdevs.com/" not in href:
                continue

            # --------------------------------
            # マスター一覧自身を除外
            # --------------------------------

            if (
                href.rstrip("/")
                == MAKER_DEVS_URL.rstrip("/")
            ):
                continue

            # --------------------------------
            # 重複除外
            # --------------------------------

            if href in seen_urls:
                continue

            seen_urls.add(href)

            # --------------------------------
            # 既取得
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
            # 明らかなナビゲーション除外
            # --------------------------------

            excluded_titles = {
                "home",
                "about",
                "contact",
                "login",
                "register",
                "search",
                "next",
                "previous",
                "back",
            }

            if title.lower() in excluded_titles:
                continue

            # --------------------------------
            # 分類
            # --------------------------------

            category = classify_makerdevs(
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
                    "source": "Maker Devs",
                }
            )

        print(
            f"[Maker Devs] New: "
            f"{len(adopted_items)}"
        )

        return (
            adopted_items,
            new_seen,
        )

    except Exception as e:

        print(
            f"[Maker Devs] Error: {e}"
        )

        return [], seen
