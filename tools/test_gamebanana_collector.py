import unittest
import xml.etree.ElementTree as ET

from sources.community_gamebanana import classify, extract_feed_entries


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

    def test_extracts_mods_and_tools_but_not_questions_or_wips(self):
        xml = """<?xml version="1.0"?>
        <rss version="2.0"><items>
          <title>GameBanana API RSS Feed</title>
          <item><title>Fantasy Tileset Pack</title><link>https://gamebanana.com/mods/100</link></item>
          <item><title>Editor error</title><link>https://gamebanana.com/questions/101</link></item>
          <item><title>My game demo</title><link>https://gamebanana.com/wips/102</link></item>
          <item><title>Plugin helper</title><link>https://gamebanana.com/tools/103</link></item>
          <item><title>Sound pack</title><link>https://gamebanana.com/sounds/104</link></item>
        </items></rss>"""
        entries = extract_feed_entries(xml)
        self.assertEqual(
            entries,
            [
                {"title": "Fantasy Tileset Pack", "link": "https://gamebanana.com/mods/100"},
                {"title": "Plugin helper", "link": "https://gamebanana.com/tools/103"},
                {"title": "Sound pack", "link": "https://gamebanana.com/sounds/104"},
            ],
        )

    def test_non_rss_response_is_rejected(self):
        with self.assertRaises(ET.ParseError):
            extract_feed_entries("<html>blocked</html>")


if __name__ == "__main__":
    unittest.main()
