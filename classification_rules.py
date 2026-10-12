"""Tunable classification vocabulary and scoring weights.

Edit these pattern dictionaries when adjusting the classifier's vocabulary.
The scoring and confidence algorithm lives in classification_scoring.py.
"""

CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"
CONFIDENCE_UNKNOWN = "unknown"


SOUND_TYPES = ("BGM", "BGS", "ME", "SE")


# RPG Makerの短い略語は、多言語文章中の普通の単語と区別する。
# 大文字表記を前提とし、英字・数字の単語内部にはマッチさせない。
SHORT_ABBREVIATIONS = ("BGM", "BGS", "ME", "SE")

FIELD_WEIGHTS = {
    "title": 5,
    "source_tags": 4,
    "category": 3,
    "description": 3,
    "body_text": 4,
    "url": 2,
    "asset_tags": 2,
}


SOUND_PATTERNS = {
    "BGM": (
        (r"\bbgm\b", 5, "explicit:BGM"),
        (r"background music", 5, "explicit:background music"),
        (r"\btheme music\b", 4, "theme music"),
        (r"\bsoundtrack\b", 3, "soundtrack"),
        (r"\bost\b", 3, "OST"),
        (r"\bmusic\b", 1, "generic:music"),
        (r"音楽", 4, "ja:音楽"),
        (r"BGM", 5, "ja:BGM"),
    ),
    "BGS": (
        (r"\bbgs\b", 5, "explicit:BGS"),
        (r"background sound", 5, "background sound"),
        (r"ambient sound", 4, "ambient sound"),
        (r"ambience", 4, "ambience"),
        (r"environmental sound", 4, "environmental sound"),
        (r"環境音", 5, "ja:環境音"),
        (r"BGS", 5, "ja:BGS"),
    ),
    "ME": (
        (r"\bme\b", 5, "explicit:ME"),
        (r"music effect", 5, "music effect"),
        (r"jingle", 4, "jingle"),
        (r"fanfare", 4, "fanfare"),
        (r"victory", 3, "victory"),
        (r"defeat", 3, "defeat"),
        (r"game over", 3, "game over"),
        (r"ジングル", 4, "ja:ジングル"),
        (r"ファンファーレ", 4, "ja:ファンファーレ"),
        (r"ME", 5, "ja:ME"),
    ),
    "SE": (
        # SEはRPG Makerの略語として大文字表記された場合だけ明示認識する。
        # フランス語の「se」と区別するため、ここだけ大文字小文字を区別する。
        (r"(?<![A-Za-z0-9])SE(?![A-Za-z0-9])", 5, "explicit:SE"),
        (r"\bsfx\b", 5, "SFX"),
        (r"sound effect", 5, "sound effect"),
        (r"sound effects", 5, "sound effects"),
        (r"foley", 4, "foley"),
        (r"sound fx", 4, "sound fx"),
        (r"効果音", 5, "ja:効果音"),
    ),
}

GRAPHIC_PATTERNS = {
    "character": (("character", 5), ("charset", 5), ("character sheet", 6), ("sprite", 4), ("sprites", 4), ("キャラクター", 5), ("キャラセット", 6)),
    "sv_character": (("sv character", 6), ("sv battler", 6), ("side-view character", 6), ("sv戦闘", 6), ("svキャラ", 6)),
    "enemy_battler": (("enemy battler", 6), ("enemy sprite", 5), ("monster sprite", 5), ("enemy", 5), ("敵キャラ", 5), ("敵キャラクター", 5)),
    "face": (("faceset", 6), ("face set", 6), ("face graphic", 6), ("face graphics", 6), ("顔グラフィック", 6)),
    "bust": (("bust", 5), ("bustup", 6), ("bust up", 6), ("バストアップ", 6)),
    "full_art": (("full art", 6), ("key art", 6), ("illustration", 4), ("concept art", 4), ("全身", 5)),
    "tileset": (("tileset", 6), ("tile set", 6), ("tilemap", 5), ("tilesheet", 6), ("tile sheet", 6), ("tiles", 3), ("タイルセット", 6), ("マップチップ", 6)),
    "battle_background": (("battleback", 6), ("battle background", 6), ("戦闘背景", 6)),
    "parallax": (("parallax", 6), ("遠景", 6), ("パララックス", 6)),
    "animation": (("animation", 5), ("effekseer", 6), ("アニメーション", 6)),
    "icon": (("icon", 5), ("icons", 5), ("icon set", 6), ("icon pack", 6), ("アイコン", 5)),
    "ui_system": (("ui", 5), ("user interface", 6), ("window skin", 6), ("windowskin", 6), ("system graphic", 6), ("システム", 4), ("ui素材", 6)),
    "title": (("title screen", 6), ("title graphic", 6), ("title logo", 6), ("タイトル", 4)),
}

PLUGIN_PATTERNS = {
    "system_core": (("core", 5), ("system", 4), ("utility", 3), ("engine", 3), ("コア", 5), ("システム", 4)),
    "battle": (
        ("battle", 5), ("combat", 5), ("action battle", 6),
        ("atb", 6), ("ctb", 6), ("bataille", 5),
        ("戦闘", 5), ("バトル", 5),
    ),
    "skills_states": (
        ("skill", 5), ("skills", 5), ("state", 5), ("states", 5),
        ("buff", 5), ("debuff", 5), ("compétence", 5),
        ("compétences", 5), ("état", 5),
        ("スキル", 5), ("ステート", 5),
    ),
    "menu_ui": (
        ("menu", 5), ("menus", 5), ("hud", 5), ("ui", 5),
        ("window", 4), ("status menu", 6),
        ("écran titre", 5), ("fenêtre", 4),
        ("メニュー", 5), ("ウィンドウ", 4),
    ),
    "items_equipment": (
        ("item", 5), ("items", 5), ("equipment", 5), ("equip", 5),
        ("équipement", 5), ("équipements", 5),
        ("objet", 5), ("objets", 5),
        ("アイテム", 5), ("装備", 5),
    ),
    "shop": (("shop", 6), ("merchant", 5), ("ショップ", 6), ("店", 4)),
    "character_party": (
        ("party", 5), ("actor", 5), ("actors", 5), ("formation", 5),
        ("équipe", 5), ("personnage jouable", 5),
        ("パーティ", 5), ("アクター", 5), ("隊列", 5),
    ),
    "quest": (
        ("quest", 6), ("journal", 5), ("mission", 5),
        ("quête", 6), ("quêtes", 6),
        ("クエスト", 6), ("ミッション", 5),
    ),
    "map_events": (
        ("map", 4), ("maps", 4), ("event", 5), ("events", 5),
        ("carte", 4), ("événement", 5), ("événements", 5),
        ("mouvement", 4), ("déplacement", 4),
        ("panorama", 4), ("fog", 4),
        ("マップ", 4), ("イベント", 5),
    ),
    "save_load": (
        ("save", 5), ("load", 5), ("autosave", 6),
        ("sauvegarde", 5), ("charger", 5),
        ("セーブ", 5), ("ロード", 5),
    ),
    "messages_dialogue": (
        ("message", 5), ("messages", 5), ("dialogue", 5),
        ("dialog", 5), ("text", 3),
        ("dialogues", 5), ("texte", 3),
        ("メッセージ", 5), ("会話", 5),
    ),
    "audio": (
        ("audio", 5), ("sound", 5), ("bgm", 6), ("bgs", 6),
        ("sfx", 6), ("musique", 5), ("音声", 5), ("音楽", 5),
    ),
    "graphics": (
        ("graphic", 5), ("graphics", 5), ("sprite", 5),
        ("picture", 5), ("animation", 5),
        ("graphisme", 5), ("graphismes", 5), ("image", 5),
        ("images", 5), ("アニメーション", 5),
        ("画像", 5), ("スプライト", 5),
    ),
    "database": (
        ("database", 6), ("notetag", 6), ("db", 6),
        ("base de données", 6),
        ("データベース", 6), ("メモタグ", 6),
    ),
    "development_debug": (
        ("debug", 6), ("developer", 5), ("development", 5),
        ("développeur", 5), ("développement", 5),
        ("débogage", 6), ("console", 5), ("test", 3),
        ("outil d'aide au développeur", 6),
        ("デバッグ", 6), ("開発", 5),
    ),
    "network_external": (
        ("network", 6), ("api", 6), ("http", 6), ("web", 5),
        ("discord", 5), ("integration", 5), ("external", 4),
        ("réseau", 6), ("intégration", 5),
        ("連携", 5),
    ),
}
