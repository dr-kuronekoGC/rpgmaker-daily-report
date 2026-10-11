import unittest
from types import SimpleNamespace
from unittest.mock import patch

from sources import community_rpg_refuge as source


RSS_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>RPG Refuge test feed</title>
    <link>https://rpg-refuge.com/</link>
    <description>Fixture for collector tests</description>
    {items}
  </channel>
</rss>
"""


def rss_item(title, url):
    return (
        "<item>"
        f"<title>{title}</title>"
        f"<link>{url}</link>"
        "<guid>" + url + "</guid>"
        "</item>"
    )


class RPGRefugeCollectorTests(unittest.TestCase):
    def test_normalizes_only_local_thread_urls(self):
        self.assertEqual(
            source.normalize_url(
                "https://rpg-refuge.com/threads/example-resource.123/"
            ),
            "https://rpg-refuge.com/threads/example-resource.123",
        )
        self.assertIsNone(
            source.normalize_url("https://example.com/threads/example.123/")
        )
        self.assertIsNone(
            source.normalize_url("https://rpg-refuge.com/forums/resources.57/")
        )

    def test_parses_resource_items_and_skips_templates(self):
        xml = RSS_TEMPLATE.format(items="".join([
            rss_item(
                "A useful tileset",
                "https://rpg-refuge.com/threads/useful-tileset.123/",
            ),
            rss_item(
                "Template: General Use 2D Assets",
                "https://rpg-refuge.com/threads/template.124/",
            ),
            rss_item(
                "External link",
                "https://example.com/threads/external.125/",
            ),
        ]))

        items = source.parse_feed(xml, "RPG Refugeグラフィック素材")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "A useful tileset")
        self.assertEqual(items[0]["category"], "RPG Refugeグラフィック素材")
        self.assertEqual(items[0]["source"], "RPG Refuge")
        self.assertEqual(items[0]["language"], "en")

    def test_first_run_baselines_without_reporting_old_topics(self):
        xml = RSS_TEMPLATE.format(items=rss_item(
            "A useful plugin",
            "https://rpg-refuge.com/threads/useful-plugin.456/",
        ))

        with patch.object(source, "get_html", return_value=xml):
            with patch.object(
                source,
                "FEED_CATEGORIES",
                (( "https://rpg-refuge.com/test.rss", "RPG Refugeプラグイン"),),
            ):
                items, new_seen = source.get_items([])

        self.assertEqual(items, [])
        self.assertEqual(
            new_seen,
            ["https://rpg-refuge.com/threads/useful-plugin.456"],
        )


    def test_keeps_entries_recovered_from_malformed_feed(self):
        parsed_entry = {
            "title": "Recovered tileset",
            "link": "https://rpg-refuge.com/threads/recovered-tileset.789/",
        }
        fake_feed = SimpleNamespace(
            bozo=True,
            bozo_exception="recoverable XML warning",
            entries=[parsed_entry],
        )
        with patch.object(source.feedparser, "parse", return_value=fake_feed):
            items = source.parse_feed(
                "<rss>imperfect</rss>",
                "RPG Refugeグラフィック素材",
            )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Recovered tileset")

    def test_recovers_entries_when_rss_xml_has_mismatched_tag(self):
        malformed_xml = """<?xml version="1.0"?>
        <rss><channel>
          <item><title>Recovered tileset</title>
            <link>https://rpg-refuge.com/threads/recovered-tileset.789/</link>
            <description><p>Badly nested markup</description>
          </item>
        </channel></rss>"""
        fake_feed = SimpleNamespace(
            bozo=True,
            bozo_exception="mismatched tag",
            entries=[],
        )
        with patch.object(source.feedparser, "parse", return_value=fake_feed):
            items = source.parse_feed(
                malformed_xml,
                "RPG Refugeグラフィック素材",
            )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Recovered tileset")

    def test_invalid_feed_error_includes_parser_diagnostic(self):
        fake_feed = SimpleNamespace(
            bozo=True,
            bozo_exception="not well-formed",
            entries=[],
        )
        with patch.object(source.feedparser, "parse", return_value=fake_feed):
            with self.assertRaisesRegex(ValueError, "not well-formed"):
                source.parse_feed(
                    "<html>not RSS</html>",
                    "RPG Refugeグラフィック素材",
                )

    def test_feed_fetch_failure_is_not_swallowed(self):
        with patch.object(source, "get_html", side_effect=OSError("network down")):
            with self.assertRaises(OSError):
                source.get_items([])


if __name__ == "__main__":
    unittest.main()
