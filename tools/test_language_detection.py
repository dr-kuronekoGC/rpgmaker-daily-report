import unittest

from language import (
    detect_language,
    LANGUAGE_ENGLISH,
    LANGUAGE_ITALIAN,
    LANGUAGE_PORTUGUESE,
    LANGUAGE_RUSSIAN,
    LANGUAGE_CHINESE,
)


class LanguageDetectionTests(unittest.TestCase):
    def test_english_resource_title(self):
        self.assertEqual(detect_language(title="Free tileset pack for RPG Maker"), LANGUAGE_ENGLISH)

    def test_italian_text_precedes_english_technical_words(self):
        self.assertEqual(
            detect_language(title="Risorse grafiche gratuite per il gioco"),
            LANGUAGE_ITALIAN,
        )

    def test_portuguese_text(self):
        self.assertEqual(
            detect_language(title="Recursos gratuitos para o jogo com música"),
            LANGUAGE_PORTUGUESE,
        )

    def test_russian_cyrillic_text(self):
        self.assertEqual(
            detect_language(title="Бесплатные ресурсы для игры и плагины"),
            LANGUAGE_RUSSIAN,
        )

    def test_chinese_traditional_text(self):
        self.assertEqual(
            detect_language(title="免費遊戲素材與角色圖像"),
            LANGUAGE_CHINESE,
        )


if __name__ == "__main__":
    unittest.main()
