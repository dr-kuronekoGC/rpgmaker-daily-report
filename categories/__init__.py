from .official import (
    classify_official,
)

from .reddit import (
    classify_reddit,
)

from .forum import (
    classify_forum,
)

from .steam import (
    classify_steam,
)

from .itch import (
    classify_itch,
)

from .asset import (
    classify_opengameart,
    classify_kenney,
)


# ==========================================
# 表示カテゴリ
# ==========================================

DISPLAY_CATEGORY = {


    # ----------------
    # Official
    # ----------------

    "本体ニュース": "本体ニュース",
    "UNITE": "UNITE",


    # ----------------
    # Forum
    # ----------------

    "Forum重要事項": "Forum重要事項",


    # ----------------
    # Plugin
    # ----------------

    "Forumプラグイン": "プラグイン",
    "Redditプラグイン": "プラグイン",
    "Steamプラグイン": "プラグイン",


    # ----------------
    # Material
    # ----------------

    "Forum素材": "素材",
    "Reddit素材": "素材",
    "itch素材": "素材",
    "OpenGameArt素材": "素材",
    "Kenney素材": "素材",


    # ----------------
    # Game
    # ----------------

    "Forum作品": "ゲーム",
    "Redditゲーム": "ゲーム",
    "itchゲーム": "ゲーム",
    "Steamゲーム": "ゲーム",


    # ----------------
    # Tips
    # ----------------

    "RedditTips": "Tips",


    # ----------------
    # Question
    # ----------------

    "Forum質問": "質問",
    "Reddit質問": "質問",

}
