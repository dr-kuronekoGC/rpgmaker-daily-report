# ==========================================
# 表示カテゴリ
# ==========================================

DISPLAY_CATEGORY = {

    # ---------- 公式 ----------
    "本体ニュース": "本体ニュース",
    "UNITE": "UNITE",
    "Forum重要事項": "Forum重要事項",

    # ---------- プラグイン ----------
    "Forumプラグイン": "プラグイン",
    "Redditプラグイン": "プラグイン",

    # ---------- 素材 ----------
    "Forum素材": "素材",
    "グラフィック": "素材",
    "サウンド": "素材",

    # ---------- ゲーム ----------
    "Forum作品": "ゲーム",
    "RPGツクール製ゲーム": "ゲーム",

    # ---------- Tips ----------
    "Tips": "Tips",

    # ---------- 質問 ----------
    "Forum質問": "質問",
}

# ==========================================
# Reddit
# ==========================================

QUESTION_WORDS = (
    "help",
    "need help",
    "looking for",
    "question",
    "how to",
    "how do",
    "can i",
    "which",
    "what",
    "thoughts?",
    "any suggestions",
    "recommendation",
    "recommendations",
)

IGNORE_WORDS = (
    "screenshot saturday",
    "megathread",
    "weekly thread",
)

REDDIT_CATEGORY_KEYWORDS = {

    "RPGツクール製ゲーム": (
        "released",
        "release",
        "steam page",
        "trailer",
        "demo",
        "now out",
        "available now",
        "launch",
        "launched",
        "steam store page",
    ),

    "プラグイン": (
        "plugin",
        "script",
        "system plugin",
        "plugin finder",
    ),

    "グラフィック": (
        "tileset",
        "sprite",
        "asset pack",
        "character generator",
        "animation asset",
        "portrait",
        "battler",
        "faceset",
        "character sheet",
    ),

    "サウンド": (
        "bgm",
        "music pack",
        "sound pack",
        "audio asset",
        "music",
        "sound effect",
        "sfx",
        "ambient",
    ),

    "Tips": (
        "tutorial",
        "guide",
        "tips",
        "workflow",
        "how i made",
        "devlog",
    ),
}


# ==========================================
# Forum
# ==========================================

FORUM_IMPORTANT_KEYWORDS = (
    "forum",
    "closure",
    "migration",
    "archive",
    "faq",
    "important",
    "announcement",
)

FORUM_IGNORE_KEYWORDS = (
    "favorite",
    "count",
    "music",
    "food",
    "what are you",
    "random thoughts",
    "off topic",
)

# ==========================================
# Reddit
# ==========================================

def classify_reddit(title):

    title = title.lower()

    if any(word in title for word in IGNORE_WORDS):
        return None

    if any(word in title for word in QUESTION_WORDS):
        return None

    for category, keywords in REDDIT_CATEGORY_KEYWORDS.items():

        if any(keyword in title for keyword in keywords):
            return category

    return None


# ==========================================
# Official
# ==========================================

def classify_official(title):

    title = title.lower()

    if "unite" in title:
        return "UNITE"

    return "本体ニュース"


# ==========================================
# Forum
# ==========================================

def classify_forum(title):

    title = title.lower()

    # ------------------------
    # Forum重要事項
    # ------------------------

    important_keywords = (
        "forum",
        "closure",
        "migration",
        "archive",
        "faq",
        "announcement",
        "shutdown",
    )

    if any(word in title for word in important_keywords):
        return "Forum重要事項"

    # ------------------------
    # 雑談除外
    # ------------------------

    ignore_keywords = (
        "farewell",
        "favorite",
        "what's your",
        "what is your",
        "real quick",
        "food",
        "color",
        "count",
        "forum game",
        "random",
        "off topic",
        "the end",
        "best friend",
        "memories",
    )

    if any(word in title for word in ignore_keywords):
        return None

    return "Forum"
