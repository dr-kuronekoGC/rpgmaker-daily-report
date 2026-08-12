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

        print(
            f"[VisuStella] HTML length: {len(html)}"
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

        print(
            f"[VisuStella] Game cells: "
            f"{len(game_cells)}"
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

            # VisuStella以外へのリンクを除外
            if "visustellamz.itch.io/" not in href:
                continue

            # トップページ自身を除外
            if (
                href.rstrip("/")
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
            # デバッグ
            # --------------------------------

            print(
                f"[VisuStella][DEBUG] "
                f"{title} -> {href}"
            )

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
                f"[VisuStella]"
                f"[{category}] "
                f"{title}"
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
