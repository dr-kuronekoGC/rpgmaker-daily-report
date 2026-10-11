import unittest

from sources.community_rpgmaker_fr import classify, extract_items, normalize_url


class FrenchCommunityTests(unittest.TestCase):
    def test_normalizes_only_resource_topic_urls(self):
        self.assertEqual(
            normalize_url("/t1234-mon-plugin"),
            "https://forum.rpgmakervx-fr.com/t1234-mon-plugin",
        )
        self.assertIsNone(
            normalize_url("https://example.com/t1234-external")
        )
        self.assertIsNone(
            normalize_url("/f127-tileset")
        )

    def test_classifies_resource_topics(self):
        self.assertEqual(
            classify("Plugin de combat"),
            "RPG Maker FRプラグイン",
        )
        self.assertEqual(
            classify("Tileset de forêt"),
            "RPG Maker FRグラフィック素材",
        )
        self.assertIsNone(
            classify("Recherche de tileset")
        )

    def test_extracts_only_recognized_resource_topics(self):
        html = """
        <a href="/t1234-plugin-de-combat">Plugin de combat</a>
        <a href="/t1235-tileset-foret">Tileset forêt</a>
        <a href="/t1236-recherche-tileset">Recherche de tileset</a>
        <a href="/f127-tileset">Tileset</a>
        """
        items = extract_items(html)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["language"], "fr")


if __name__ == "__main__":
    unittest.main()
