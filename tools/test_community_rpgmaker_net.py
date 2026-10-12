import unittest

from sources import community_rpgmaker_net as source


class RPGMakerNetworkTests(unittest.TestCase):
    def test_normalizes_only_local_urls(self):
        self.assertEqual(
            source.normalize_url("https://rpgmaker.net/games/1234/"),
            "https://rpgmaker.net/games/1234/",
        )
        self.assertIsNone(source.normalize_url("https://example.com/resources/"))

    def test_extracts_resource_related_links_and_skips_questions(self):
        html = """
        <html><body>
          <div><a href="/resources/123/">Fantasy Tileset Pack</a></div>
          <div><a href="/resources/124/">Help looking for a tileset</a></div>
          <div><a href="/games/125/">A game showcase</a></div>
        </body></html>
        """
        items = source.extract_items(html)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Fantasy Tileset Pack")
        self.assertEqual(items[0]["language"], "en")


if __name__ == "__main__":
    unittest.main()
