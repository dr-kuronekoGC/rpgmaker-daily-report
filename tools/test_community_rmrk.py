import unittest

from sources import community_rmrk as source


class RMRKCollectorTests(unittest.TestCase):
    def test_normalizes_only_rmrk_topic_urls(self):
        self.assertEqual(
            source.normalize_url("https://rmrk.net/index.php?topic=123.0"),
            "https://rmrk.net/index.php?topic=123.0",
        )
        self.assertIsNone(source.normalize_url("https://example.com/index.php?topic=123.0"))
        self.assertIsNone(source.normalize_url("https://rmrk.net/index.php?board=114.0"))

    def test_classifies_resource_topics_and_skips_requests(self):
        self.assertEqual(source.classify("Fantasy Tileset Pack"), "RMRKグラフィック素材")
        self.assertEqual(source.classify("Original Battle Music"), "RMRKサウンド素材")
        self.assertEqual(source.classify("RGSS Script Collection"), "RMRKプラグイン・スクリプト")
        self.assertIsNone(source.classify("[Request] Need a tileset"))

    def test_extracts_resource_topic_links(self):
        html = """
        <table><tr><td class="subject">
          <a href="index.php?topic=123.0">Fantasy Tileset Pack</a>
        </td></tr><tr><td class="subject">
          <a href="https://example.com/topic=456">External asset</a>
        </td></tr></table>
        """
        items = source.extract_items(html)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://rmrk.net/index.php?topic=123.0")
        self.assertEqual(items[0]["language"], "en")


if __name__ == "__main__":
    unittest.main()
