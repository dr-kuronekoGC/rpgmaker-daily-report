# ==========================================
# OpenGameArt
# ==========================================

from config import (
    OPENGAMEART_URL,
    OPENGAMEART_SEEN_FILE,
)

from categories.assets import classify_asset
from sources.html import collect_html


SEEN_FILE = OPENGAMEART_SEEN_FILE


def is_opengameart_item(url):
    """
    OpenGameArtの実際の作品ページだけを対象にする。
    """

    return (
        "/content/" in url
    )


def get_items(seen):

    return collect_html(
        url=OPENGAMEART_URL,
        seen=seen,

        classify=classify_asset,

        # ナビゲーションではなく、
        # コンテンツページのリンクだけを見る
        selector="a[href*='/content/']",

        source_name="OpenGameArt",

        href_filter=is_opengameart_item,
    )
