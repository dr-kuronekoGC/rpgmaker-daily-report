import unittest

from sources.community_gamebanana import classify, get_tags


class GameBananaCollectorTests(unittest.TestCase):
    def test_classifies_reusable_graphics(self):
        self.assertEqual(
            classify("Fantasy Tileset Pack"),
            "GameBananaグラフィック素材",
        )

    def test_classifies_plugins_and_tools(self):
        self.assertEqual(
            classify("RPG Maker MZ Plugin - Better Menu"),
            "GameBananaプラグイン・ツール",
        )

    def test_classifies_audio(self):
        self.assertEqual(
            classify("Ambient Music Pack"),
            "GameBananaサウンド素材",
        )

    def test_excludes_questions_and_requests(self):
        self.assertIsNone(classify("Looking for a character sprite"))
        self.assertIsNone(classify("Help with plugin installation"))

    def test_excludes_game_showcases(self):
        self.assertIsNone(classify("My Game Showcase - New Demo Release"))

    def test_ignores_unclassified_posts(self):
        self.assertIsNone(classify("RPG Maker MV update discussion"))

    def test_reads_feed_tags(self):
        entry = {
            "tags": [{"term": "tileset"}, {"term": "RPG Maker"}],
            "categories": ["graphics"],
        }
        self.assertEqual(get_tags(entry), "tileset RPG Maker graphics")


if __name__ == "__main__":
    unittest.main()
