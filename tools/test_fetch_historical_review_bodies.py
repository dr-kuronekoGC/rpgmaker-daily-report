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

    def test_invision_query_topic_url_uses_explicit_controller_route(self):
        self.assertEqual(
            MODULE.invision_query_topic_url(
                "https://www.rpg2s.it/forum/index.php?/topic/24040-icone-mz-stile/"
            ),
            "https://www.rpg2s.it/forum/index.php?app=forums&module=forums&controller=topic&id=24040",
        )
        self.assertIsNone(MODULE.invision_query_topic_url("https://example.com/forum/topic/no-id/"))

    def test_rmrk_wayback_fallback_recovers_body_and_resolves_links_to_original_host(self):
        original_url = "https://rmrk.net/index.php?topic=48165.0"
        original = {
            "http_status": 200,
            "body_text": "",
            "outbound_links": [],
            "html_diagnostics": {
                "body_source": "empty",
                "html_chars": 998,
                "body_text_chars": 0,
            },
        }
        cdx = json.dumps([
            ["timestamp", "original", "statuscode", "mimetype"],
            ["20250101000000", original_url, "200", "text/html"],
        ])
        archived_html = """
        <html><head><title>Actors 8D sprites? [SOLVED]</title></head>
        <body><div id="forumposts"><div class="postarea">
          <div class="message">
            The original topic asks where to find reusable character sets for RPG Maker.
            A later reply identifies the source and links to a downloadable sprite archive.
          </div>
          <a href="/files/actors.zip">Download actor sprites</a>
        </div></div></body></html>
        """

        class FakeResponse:
            def __init__(self, text, url):
                self.text = text
                self.status_code = 200
                self.url = url

            def raise_for_status(self):
                return None

        class FakeSession:
            def get(self, url, *args, **kwargs):
                if "web.archive.org/cdx/search/cdx" in url:
                    return FakeResponse(cdx, url)
                return FakeResponse(
                    archived_html,
                    "https://web.archive.org/web/20250101000000id_/" + original_url,
                )

        result = MODULE.try_wayback_fallback(FakeSession(), original_url, original)
        self.assertEqual(result["retrieval_method"], "wayback_archive_fallback")
        self.assertTrue(result["html_diagnostics"]["wayback_used"])
        self.assertIn("reusable character sets", result["body_text"])
        self.assertTrue(
            any(link["url"] == "https://rmrk.net/files/actors.zip"
                for link in result["outbound_links"])
        )

    def test_rmrk_wayback_fallback_keeps_original_when_no_snapshot_exists(self):
        original_url = "https://rmrk.net/index.php?topic=48165.0"
        original = {
            "http_status": 200,
            "body_text": "",
            "outbound_links": [],
            "html_diagnostics": {
                "body_source": "empty",
                "html_chars": 998,
                "body_text_chars": 0,
            },
        }

        class FakeResponse:
            text = json.dumps([["timestamp", "original", "statuscode", "mimetype"]])
            status_code = 200
            url = "https://web.archive.org/cdx/search/cdx"

            def raise_for_status(self):
                return None

        class FakeSession:
            def get(self, *args, **kwargs):
                return FakeResponse()

        result = MODULE.try_wayback_fallback(FakeSession(), original_url, original)
        self.assertIs(result, original)
        self.assertFalse(result["html_diagnostics"]["wayback_snapshot_found"])

    def test_invision_query_fallback_uses_better_post_body(self):
        original_url = "https://www.rpg2s.it/forum/index.php?/topic/123-example/"
        original = {
            "http_status": 200,
            "body_text": "Login warning Example topic By Author in Grafica",
            "outbound_links": [],
            "html_diagnostics": {
                "body_source": "#ipsLayout_mainArea",
                "body_text_chars": 48,
            },
        }
        html = """
        <html><head><title>Example topic</title></head>
        <body><div id="ipsLayout_mainArea">
          <div class="ipsComment_content">
            <p>This is the original resource post with enough content to show the
            actual post body instead of the short topic header. The plugin download
            link is provided below for users to retrieve the file.</p>
            <a href="/files/plugin.js">Download plugin</a>
          </div>
        </div></body></html>
        """

        class FakeResponse:
            text = html
            status_code = 200
            url = (
                "https://www.rpg2s.it/forum/index.php?"
                "app=forums&module=forums&controller=topic&id=123"
            )

            def raise_for_status(self):
                return None

        class FakeSession:
            def get(self, *args, **kwargs):
                return FakeResponse()

        result = MODULE.try_invision_query_fallback(
            FakeSession(),
            original_url,
            original,
        )
        self.assertEqual(result["retrieval_method"], "html_invision_query_fallback")
        self.assertEqual(result["requested_url"], original_url)
        self.assertEqual(result["html_diagnostics"]["body_source"], ".ipsComment_content")
        self.assertTrue(result["html_diagnostics"]["alternate_route_used"])
        self.assertTrue(
            any(link["url"] == "https://www.rpg2s.it/files/plugin.js"
                for link in result["outbound_links"])
        )

    def test_invision_query_fallback_keeps_original_when_alternate_is_not_better(self):
        original_url = "https://www.rpg2s.it/forum/index.php?/topic/123-example/"
        original = {
            "http_status": 200,
            "body_text": "Login warning Example topic By Author in Grafica",
            "outbound_links": [],
            "html_diagnostics": {
                "body_source": "#ipsLayout_mainArea",
                "body_text_chars": 48,
            },
        }
        html = """
        <html><head><title>Example topic</title>
        <meta name="description" content="Short topic description."></head>
        <body><div id="ipsLayout_mainArea">Login warning Example topic By Author in Grafica</div></body></html>
        """

        class FakeResponse:
            text = html
            status_code = 200
            url = (
                "https://www.rpg2s.it/forum/index.php?"
                "app=forums&module=forums&controller=topic&id=123"
            )

            def raise_for_status(self):
                return None

        class FakeSession:
            def get(self, *args, **kwargs):
                return FakeResponse()

        result = MODULE.try_invision_query_fallback(
            FakeSession(),
            original_url,
            original,
        )
        self.assertIs(result, original)
        self.assertFalse(result["html_diagnostics"]["alternate_route_used"])

    def test_invision_main_area_fallback_extracts_post_text_and_download_links(self):
        html = """
        <html>
          <head>
            <title>Example Invision topic</title>
            <meta name="description" content="Short metadata excerpt only.">
            <script>const legacyClass = "ipsType_richText";</script>
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
        self.assertTrue(result["html_diagnostics"]["body_node_found"])
        self.assertEqual(result["html_diagnostics"]["body_source"], "#ipsLayout_mainArea")
        self.assertGreater(result["html_diagnostics"]["html_chars"], 100)
        self.assertIn("attached plugin", result["html_diagnostics"]["body_excerpt"])
        self.assertTrue(result["html_diagnostics"]["raw_has_invision_post_classes"])
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
