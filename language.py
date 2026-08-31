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

    外部APIは使用せず、文字種を中心に
    軽量に判定する。

    判定できない場合は None を返す。
    """

    tags = tags or []

    text = " ".join(
        [
            str(title or ""),
            str(description or ""),
            " ".join(
                str(tag)
                for tag in tags
            ),
        ]
    )

    if not text.strip():
        return None

    # ======================================
    # 日本語
    # ======================================

    if re.search(
        r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]",
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

    if re.search(
        r"[\u4e00-\u9fff]",
        text,
    ):
        return LANGUAGE_CHINESE

    # ======================================
    # ラテン系言語
    #
    # ここは誤判定を避けるため、
    # 現段階では明確な特徴がある場合のみ判定する。
    # ======================================

    lower_text = text.lower()

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
        " français",
        " française",
    ]

    if any(
        marker in f" {lower_text} "
        for marker in french_markers
    ):
        return LANGUAGE_FRENCH

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
        " deutsch",
    ]

    if any(
        marker in f" {lower_text} "
        for marker in german_markers
    ):
        return LANGUAGE_GERMAN

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
        " español",
        " española",
    ]

    if any(
        marker in f" {lower_text} "
        for marker in spanish_markers
    ):
        return LANGUAGE_SPANISH

    # ======================================
    # 英語
    #
    # 明確な英語語彙が複数ある場合のみ判定。
    # ======================================

    english_markers = [
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
        " game ",
        " asset ",
        " resource ",
        " question ",
        " tutorial ",
    ]

    english_count = sum(
        1
        for marker in english_markers
        if marker in f" {lower_text} "
    )

    if english_count >= 2:
        return LANGUAGE_ENGLISH

    return None
