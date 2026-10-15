import unittest
from unittest.mock import Mock, patch
from contextlib import redirect_stdout
from io import StringIO

from sources.community_gamebanana import classify, extract_feed_entries, get_items
from config import GAMEBANANA_RSS_URLS


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

    def test_fetches_mv_and_mz_feeds_separately(self):
        xml = """<?xml version="1.0"?>
        <rss version="2.0"><items>
          <item><title>Fantasy Tileset Pack</title><link>https://gamebanana.com/mods/100</link></item>
        </items></rss>"""
        responses = []
        for _ in GAMEBANANA_RSS_URLS:
            response = Mock()
            response.content = xml.encode("utf-8")
            response.raise_for_status.return_value = None
            responses.append(response)

        with patch("sources.community_gamebanana.requests.get", side_effect=responses) as get:
            items, seen = get_items([])

        self.assertEqual(get.call_count, 2)
        self.assertEqual([call.args[0] for call in get.call_args_list], list(GAMEBANANA_RSS_URLS))
        # Initial collection establishes a baseline rather than flooding Slack.
        self.assertEqual(items, [])
        self.assertEqual(seen, ["https://gamebanana.com/mods/100"])

    def test_logs_feed_counts_and_classification_counts(self):
        xml = """<?xml version="1.0"?>
        <rss version="2.0"><items>
          <item><title>Fantasy Tileset Pack</title><link>https://gamebanana.com/mods/100</link></item>
          <item><title>RPG Maker update discussion</title><link>https://gamebanana.com/tools/101</link></item>
        </items></rss>"""
        responses = []
        for _ in GAMEBANANA_RSS_URLS:
            response = Mock()
            response.content = xml.encode("utf-8")
            response.raise_for_status.return_value = None
            responses.append(response)

        output = StringIO()
        with patch("sources.community_gamebanana.requests.get", side_effect=responses):
            with redirect_stdout(output):
                items, seen = get_items(["https://gamebanana.com/mods/old"])

        self.assertEqual(len(items), 1)
        self.assertEqual(len(seen), 4)
        self.assertIn("valid entries=2", output.getvalue())
        self.assertIn("new classified=1", output.getvalue())
        self.assertIn("new unclassified=1", output.getvalue())

    def test_non_rss_response_is_rejected(self):
        with self.assertRaises(ValueError):
            extract_feed_entries("<html>blocked</html>")


if __name__ == "__main__":
    unittest.main()
