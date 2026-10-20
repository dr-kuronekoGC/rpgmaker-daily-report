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
