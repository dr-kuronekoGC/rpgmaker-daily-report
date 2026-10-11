import unittest

from sources.community_rpgmaker_ru import classify, normalize_url


class RussianCommunityTests(unittest.TestCase):
    def test_accepts_only_rpgmaker_forum_threads(self):
        self.assertEqual(
            normalize_url("https://rpgmaker.ru/forum/example-12345/"),
            "https://rpgmaker.ru/forum/example-12345",
        )
        self.assertIsNone(normalize_url("https://example.com/forum/example-12345/"))

    def test_classifies_plugin_and_skips_questions(self):
        self.assertEqual(classify("[MZ] FS Layer management lite"), None)
        self.assertIsNone(classify("Ищу плагин для отражений в MZ"))


if __name__ == "__main__":
    unittest.main()
