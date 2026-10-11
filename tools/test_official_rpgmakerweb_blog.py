import unittest

from official_rpgmakerweb_blog import extract_blog_items, normalize_article_url


class OfficialRPGMakerWebBlogTests(unittest.TestCase):
    def test_normalizes_only_official_blog_article_urls(self):
        self.assertEqual(
            normalize_article_url("/blog/new-resource-pack?ref=home"),
            "https://www.rpgmakerweb.com/blog/new-resource-pack",
        )
        self.assertIsNone(
            normalize_article_url("https://example.com/blog/new-resource-pack")
        )
        self.assertIsNone(
            normalize_article_url("/category/resources")
        )

    def test_extracts_unique_article_links_and_ignores_navigation(self):
        html = """
        <html><body>
          <a href="/blog/new-tileset"><img alt="New Tileset Pack"></a>
          <a href="/blog/new-tileset">New Tileset Pack</a>
          <a href="/blog/plugin-update">Plugin Update</a>
          <a href="/category/resources">Resources</a>
          <a href="/blog/new-audio">Read More</a>
          <a href="https://example.com/blog/external">External</a>
        </body></html>
        """
        items = extract_blog_items(html)

        self.assertEqual(
            [item["url"] for item in items],
            [
                "https://www.rpgmakerweb.com/blog/new-tileset",
                "https://www.rpgmakerweb.com/blog/plugin-update",
            ],
        )
        self.assertEqual(items[0]["title"], "New Tileset Pack")
        self.assertEqual(items[0]["source"], "RPG Maker Web Blog")
        self.assertEqual(items[0]["category"], "海外公式ブログ情報")

    def test_skips_seen_article_urls(self):
        html = '<a href="/blog/old-post">Old Post</a><a href="/blog/new-post">New Post</a>'
        items = extract_blog_items(
            html,
            {"https://www.rpgmakerweb.com/blog/old-post"},
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "New Post")


if __name__ == "__main__":
    unittest.main()
