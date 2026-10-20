import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("fetch_historical_review_bodies.py")
SPEC = importlib.util.spec_from_file_location("historical_body_audit", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class HistoricalBodyAuditTests(unittest.TestCase):
    def test_text_is_normalized(self):
        self.assertEqual(MODULE.clean_text("  a \n b\t c  "), "a b c")

    def test_non_public_urls_are_rejected(self):
        self.assertFalse(MODULE.is_public_http_url("file:///etc/passwd"))
        self.assertFalse(MODULE.is_public_http_url("http://127.0.0.1/test"))
        self.assertFalse(MODULE.is_public_http_url("http://localhost/test"))

    def test_public_http_url_is_accepted(self):
        self.assertTrue(MODULE.is_public_http_url("https://www.reddit.com/r/RPGMaker/"))

    def test_invision_main_area_fallback_extracts_post_text_and_download_links(self):
        html = """
        <html>
          <head>
            <title>Example Invision topic</title>
            <meta name="description" content="Short metadata excerpt only.">
          </head>
          <body>
            <div id="ipsLayout_mainArea">
              <div class="ipsBox">
                <p>This is a resource post with enough text to represent the original post.
                The attached plugin is available from the download link below.</p>
                <a href="/files/PluginCore.js">Download plugin</a>
              </div>
            </div>
          </body>
        </html>
        """

        class FakeResponse:
            text = html
            status_code = 200
            url = "https://www.rpg2s.it/forum/index.php?/topic/123-example/"

            def raise_for_status(self):
                return None

        class FakeSession:
            def get(self, *args, **kwargs):
                return FakeResponse()

        result = MODULE.parse_html(
            FakeSession(),
            "https://www.rpg2s.it/forum/index.php?/topic/123-example/",
        )
        self.assertIn("attached plugin", result["body_text"])
        self.assertNotEqual(result["body_text"], "Short metadata excerpt only.")
        self.assertTrue(
            any(link["url"] == "https://www.rpg2s.it/files/PluginCore.js"
                for link in result["outbound_links"])
        )

    def test_extract_links_includes_embedded_audio_sources(self):
        node = MODULE.BeautifulSoup(
            '<div><audio controls><source src="/media/music/forest.ogg" '
            'type="audio/ogg"></audio></div>',
            "html.parser",
        )
        links = MODULE.extract_links(node, "https://rpgmaker.ru/forum/topic")
        self.assertEqual(len(links), 1)
        self.assertEqual(
            links[0]["url"],
            "https://rpgmaker.ru/media/music/forest.ogg",
        )
        self.assertEqual(links[0]["link_kind"], "media_source")

    def test_extract_links_includes_embedded_images_without_anchor(self):
        node = MODULE.BeautifulSoup(
            '<div><img src="/media/kunena/attachments/1/CharSet.png" alt="CharSet"></div>',
            "html.parser",
        )
        links = MODULE.extract_links(node, "https://rpgmaker.ru/forum/topic")
        self.assertEqual(len(links), 1)
        self.assertEqual(
            links[0]["url"],
            "https://rpgmaker.ru/media/kunena/attachments/1/CharSet.png",
        )
        self.assertEqual(links[0]["link_kind"], "embedded_image")


if __name__ == "__main__":
    unittest.main()
