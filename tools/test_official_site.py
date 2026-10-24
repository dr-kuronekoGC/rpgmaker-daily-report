import unittest

from report import build_report
from sources.official_site import (
    extract_official_news_items,
    normalize_article_url,
)


class OfficialNewsExtractionTests(unittest.TestCase):
    def test_normalizes_only_individual_official_article_urls(self):
        self.assertEqual(
            normalize_article_url("/news/4157/"),
            "https://www.rpgmakerofficial.com/news/4157/",
        )
        self.assertIsNone(
            normalize_article_url("https://example.com/news/4157/")
        )
        self.assertIsNone(
            normalize_article_url("/news/")
        )
        self.assertIsNone(
            normalize_article_url("/products/4157/")
        )

    def test_extracts_article_url_and_visible_publication_date(self):
        html = """
        <html><body>
          <div class="news-card">
            <span class="date">2026.10.20</span>
            <a href="/news/5001/">
              <h3>RPGツクールU2U 体験版を公開</h3>
            </a>
            <p>記事の概要</p>
          </div>
          <div class="news-card">
            <span class="date">2026.08.28</span>
            <h3><a href="/news/4990/">RPG Maker Special Sale 2026</a></h3>
          </div>
        </body></html>
        """
        items = extract_official_news_items(html)

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["url"], "https://www.rpgmakerofficial.com/news/5001/")
        self.assertEqual(items[0]["published_date"], "2026.10.20")
        self.assertEqual(items[0]["source"], "RPG Maker Official")
        self.assertEqual(items[1]["url"], "https://www.rpgmakerofficial.com/news/4990/")
        self.assertEqual(items[1]["published_date"], "2026.08.28")

    def test_skips_duplicate_cards_for_the_same_article(self):
        html = """
        <div><span>2026.10.20</span><a href="/news/5001/"><h3>Announcement</h3></a></div>
        <div><span>2026.10.20</span><a href="/news/5001/"><h3>Announcement</h3></a></div>
        """
        self.assertEqual(len(extract_official_news_items(html)), 1)

    def test_does_not_invent_article_url_when_link_is_missing(self):
        html = "<div><span>2026.10.20</span><h3>Announcement without a link</h3></div>"
        self.assertEqual(extract_official_news_items(html), [])

    def test_report_displays_official_article_link_and_publication_date(self):
        report = build_report(
            [
                {
                    "title": "Official announcement",
                    "url": "https://www.rpgmakerofficial.com/news/5001/",
                    "category": "本体ニュース",
                    "source": "RPG Maker Official",
                    "published_date": "2026.10.20",
                }
            ],
            review_items=[],
            carryover_items=[],
            source_results=[],
        )

        self.assertIn(
            "<https://www.rpgmakerofficial.com/news/5001/|Official announcement>",
            report,
        )
        self.assertIn("公開日：2026.10.20", report)


if __name__ == "__main__":
    unittest.main()
