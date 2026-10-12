import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from sources.html import collect_html


class TestHtmlCollectionDiagnostics(unittest.TestCase):
    def test_diagnostics_report_extraction_and_classification_counts(self):
        page_url = "https://www.gamedevmarket.net/category/2d"
        fixture = """
        <html><body>
          <a href="/category/2d">2D Category</a>
          <a href="/product/forest-tileset">Forest Tileset</a>
          <a href="/product/devlog">My Development Devlog</a>
        </body></html>
        """

        def classify(title, url):
            if "tileset" in title.lower():
                return ("グラフィック素材", [])
            return (None, [])

        output = io.StringIO()
        with patch("sources.html.get_html", return_value=fixture):
            with redirect_stdout(output):
                items, new_seen = collect_html(
                    url=page_url,
                    seen=[],
                    classify=classify,
                    selector="a[href]",
                    source_name="GameDevMarket",
                    href_filter=lambda url: (
                        "/category/" not in url
                        and url.rstrip("/") != page_url.rstrip("/")
                    ),
                    diagnostics=True,
                )

        self.assertEqual(len(items), 1)
        self.assertIn("Forest Tileset", items[0]["title"])
        self.assertEqual(len(new_seen), 1)
        log = output.getvalue()
        self.assertIn("selected_links=3", log)
        self.assertIn("filter_passed=2", log)
        self.assertIn("unseen_candidates=2", log)
        self.assertIn("classified=1", log)
        self.assertIn("rejected_by_classifier=1", log)


if __name__ == "__main__":
    unittest.main()
