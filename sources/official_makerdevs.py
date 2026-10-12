# ==========================================
# Maker Devs
# ==========================================

import requests

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

    if normalized:
        return "RPG Makerプラグイン"

    return None


# ==========================================
# Main
# ==========================================

def get_items(seen):

    try:

        # 他のHTML収集元と同じ共通HTTP設定を使う。
        # 個別User-Agentとtimeoutの違いがTLSエラーに
        # 影響しているかを切り分けるための低リスクな検証。
        html = get_html(MAKER_DEVS_URL)

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        adopted_items = []
        new_seen = seen.copy()

        seen_urls = set()

        for link in soup.select("a[href]"):

            href = link.get("href")

            if not href:
                continue

            href = urljoin(
                MAKER_DEVS_URL,
                href,
            )

            if "makerdevs.com/" not in href:
                continue

            if (
                href.rstrip("/")
                == MAKER_DEVS_URL.rstrip("/")
            ):
                continue

            if href in seen_urls:
                continue

            seen_urls.add(href)

            if href in seen:
                continue

            title = link.get_text(
                " ",
                strip=True,
            )

            if not title:
                continue

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

            category = classify_makerdevs(
                title,
                href,
            )

            if category is None:
                continue

            new_seen.append(href)

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

    except requests.exceptions.SSLError as e:

        print(
            f"[Maker Devs] SSL Error: {e}"
        )

        raise

    except requests.exceptions.RequestException as e:

        print(
            f"[Maker Devs] Request Error: {e}"
        )

        raise

    except Exception as e:

        print(
            f"[Maker Devs] Error: {e}"
        )

        raise
