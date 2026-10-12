# ==========================================
# GameDevMarket
# ==========================================

from config import (
    GAMEDEVMARKET_URL,
    GAMEDEVMARKET_SEEN_FILE,
)

from categories.assets import classify_asset
from sources.html import collect_html


SEEN_FILE = GAMEDEVMARKET_SEEN_FILE


def is_gamedevmarket_item(url):

    return (
        "/category/" not in url
        and url.rstrip("/") != GAMEDEVMARKET_URL.rstrip("/")
    )


def get_items(seen):

    # HTTPエラーを空の成功結果として扱うと、
    # Source Healthで接続失敗を検知できなくなるため、
    # 例外はmain.py側へ伝播させる。
    return collect_html(
        url=GAMEDEVMARKET_URL,
        seen=seen,
        classify=classify_asset,
        selector="a[href]",
        source_name="GameDevMarket",
        href_filter=is_gamedevmarket_item,
        diagnostics=True,
    )
