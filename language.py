import re


LANGUAGE_JAPANESE = "日本語"
LANGUAGE_ENGLISH = "英語"
LANGUAGE_FRENCH = "フランス語"
LANGUAGE_GERMAN = "ドイツ語"
LANGUAGE_SPANISH = "スペイン語"
LANGUAGE_KOREAN = "韓国語"
LANGUAGE_CHINESE = "中国語"


def detect_language(
    title="",
    description="",
    tags=None,
):
    """
    Itemのテキストから言語を推定する。

    外部APIは使用せず、文字種と
    基本的な言語特徴を利用して軽量に判定する。

    判定できない場合は None を返す。
    """

    tags = tags or []

    title_text = str(title or "")
    description_text = str(description or "")
    tag_text = " ".join(
        str(tag)
        for tag in tags
    )

    text = " ".join(
        [
            title_text,
            description_text,
            tag_text,
        ]
    ).strip()

    if not text:
        return None

    # ======================================
    # 日本語
    # ======================================

    # ひらがな・カタカナがあれば日本語と判定
    if re.search(
        r"[\u3040-\u30ff]",
        text,
    ):
        return LANGUAGE_JAPANESE

    # ======================================
    # 韓国語
    # ======================================

    if re.search(
        r"[\uac00-\ud7af]",
        text,
    ):
        return LANGUAGE_KOREAN

    # ======================================
    # 中国語
    # ======================================

    # 中国語は漢字のみの場合があるため、
    # 日本語のひらがな・カタカナがないことを確認してから判定。
    #
    # ただし、RPG Maker関連の英語タイトルに
    # 漢字が混ざるケースもあるため、
    # 中国語特有の文字を一定数含む場合を中心に判定する。

    chinese_specific_chars = re.search(
        r"[们国这为与从个来对发会时现过说还没样东华开关门书画乐龙马车]",
        text,
    )

    if chinese_specific_chars:
        return LANGUAGE_CHINESE

    # ======================================
    # ラテン系言語
    # ======================================

    lower_text = f" {text.lower()} "

    # --------------------------------------
    # フランス語
    # --------------------------------------

    french_markers = [
        " le ",
        " la ",
        " les ",
        " des ",
        " une ",
        " un ",
        " avec ",
        " pour ",
        " dans ",
        " sur ",
        " est ",
        " sont ",
        " français",
        " française",
        " télécharger",
    ]

    french_count = sum(
        1
        for marker in french_markers
        if marker in lower_text
    )

    if french_count >= 2:
        return LANGUAGE_FRENCH

    # --------------------------------------
    # ドイツ語
    # --------------------------------------

    german_markers = [
        " der ",
        " die ",
        " das ",
        " den ",
        " dem ",
        " des ",
        " und ",
        " mit ",
        " für ",
        " ist ",
        " sind ",
        " deutsch",
        " deutsche",
    ]

    german_count = sum(
        1
        for marker in german_markers
        if marker in lower_text
    )

    if german_count >= 2:
        return LANGUAGE_GERMAN

    # --------------------------------------
    # スペイン語
    # --------------------------------------

    spanish_markers = [
        " el ",
        " la ",
        " los ",
        " las ",
        " una ",
        " uno ",
        " para ",
        " con ",
        " que ",
        " por ",
        " es ",
        " son ",
        " español",
        " española",
        " descargar",
    ]

    spanish_count = sum(
        1
        for marker in spanish_markers
        if marker in lower_text
    )

    if spanish_count >= 2:
        return LANGUAGE_SPANISH

    # ======================================
    # 英語
    # ======================================

    # RPG Maker関連では、短いタイトルでも
    # 以下のような特徴語だけで英語と判断できるケースが多い。
    #
    # ただし "map" や "music" など単独では
    # 言語判定の根拠として弱いため使用しない。

    english_strong_markers = [
        " the ",
        " and ",
        " for ",
        " with ",
        " this ",
        " that ",
        " from ",
        " free ",
        " download ",
        " plugin ",
        " tileset ",
        " sprite ",
        " spritesheet ",
        " game ",
        " asset ",
        " resource ",
        " resources ",
        " pack ",
        " tutorial ",
        " character ",
        " characters ",
        " background ",
        " generator ",
        " faceset ",
        " battleback ",
    ]

    english_count = sum(
        1
        for marker in english_strong_markers
        if marker in lower_text
    )

    # 強い英語特徴語が1つでもあれば英語候補とする。
    if english_count >= 1:
        return LANGUAGE_ENGLISH

    # ======================================
    # 判定なし
    # ======================================

    return None
