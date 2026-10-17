import unittest
from unittest.mock import patch

from sources.community_rpgmaker_ru import classify, extract_items, normalize_url, get_items


class RussianCommunityTests(unittest.TestCase):
    def test_accepts_only_rpgmaker_forum_threads(self):
        self.assertEqual(
            normalize_url("https://rpgmaker.ru/forum/grafika/59747-sprite"),
            "https://rpgmaker.ru/forum/grafika/59747-sprite",
        )
        self.assertIsNone(normalize_url("https://example.com/forum/example-12345/"))

    def test_classifies_plugin_and_skips_questions(self):
        self.assertEqual(classify("[MZ] FS Layer management lite"), "プラグイン")
        self.assertIsNone(classify("Ищу плагин для отражений в MZ"))
        self.assertIsNone(classify("Нужна графика для создания мрачной атмосферы", "グラフィック素材"))

    def test_graphics_and_music_sections_are_supported(self):
        graphics = extract_items(
            '<a href="/forum/grafika/59747-sprite">Облако Ресурсов</a>',
            "グラフィック素材",
        )
        music = extract_items(
            '<a href="/forum/muzyka/60438-free-music">FREE Creative Commons Music</a>',
            "音楽素材",
        )
        self.assertEqual(graphics[0]["category"], "グラフィック素材")
        self.assertEqual(music[0]["category"], "音楽素材")
        self.assertEqual(graphics[0]["language"], "ru")

    @patch("sources.community_rpgmaker_ru.get_html")
    def test_fetches_plugins_graphics_and_music(self, mock_get_html):
        mock_get_html.side_effect = [
            '<a href="/forum/u-mz/12345-plugin">Plugin</a>',
            '<a href="/forum/grafika/23456-sprite">Sprite Pack</a>',
            '<a href="/forum/muzyka/34567-music">Music Pack</a>',
        ]
        items, seen = get_items(["existing-url"])
        self.assertEqual(len(mock_get_html.call_args_list), 3)
        self.assertEqual(
            {item["category"] for item in items},
            {"プラグイン", "グラフィック素材", "音楽素材"},
        )
        self.assertEqual(len(seen), 4)


if __name__ == "__main__":
    unittest.main()
