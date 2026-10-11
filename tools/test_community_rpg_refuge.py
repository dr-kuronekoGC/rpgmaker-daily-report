import unittest
from unittest.mock import patch

from sources import community_rpg_refuge as source


def forum_page(rows):
    return f"""<!DOCTYPE html>
    <html><head><title>Test forum</title></head><body>
      <div class="block-body">{rows}</div>
    </body></html>"""


def thread_row(title, slug, thread_id, label=""):
    label_html = f'<span class="label">{label}</span>' if label else ""
    return f"""
      <div class="structItem">
        <div class="structItem-title">
          {label_html}
          <a href="/threads/{slug}.{thread_id}/">{title}</a>
        </div>
      </div>
    """


class RPGRefugeCollectorTests(unittest.TestCase):
    def test_normalizes_only_local_thread_urls(self):
        self.assertEqual(
            source.normalize_url("https://rpg-refuge.com/threads/example-resource.123/"),
            "https://rpg-refuge.com/threads/example-resource.123",
        )
        self.assertIsNone(source.normalize_url("https://example.com/threads/example.123/"))
        self.assertIsNone(source.normalize_url("https://rpg-refuge.com/forums/resources.57/"))

    def test_parses_resource_threads_and_skips_template_or_rules_rows(self):
        external = thread_row("External link", "external", 126).replace(
            'href="/threads/external.126/"',
            'href="https://example.com/threads/external.126/"',
        )
        html = forum_page("".join([
            thread_row("A useful tileset", "useful-tileset", 123, "Tiles"),
            thread_row("General Use 2D Assets New Thread Checklist", "new-thread-checklist", 124, "Template"),
            thread_row("General Use 2D Assets Rules and Requirements", "rules-and-requirements", 125, "Rules"),
            external,
        ]))

        items = source.parse_forum_page(html, "RPG Refugeグラフィック素材")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "A useful tileset")
        self.assertEqual(items[0]["category"], "RPG Refugeグラフィック素材")
        self.assertEqual(items[0]["source"], "RPG Refuge")
        self.assertEqual(items[0]["language"], "en")

    def test_ignores_links_outside_thread_title_elements(self):
        html = forum_page(
            '<a href="/threads/featured-thread.900/">Featured thread</a>'
            + thread_row("Actual resource", "actual-resource", 901)
        )
        items = source.parse_forum_page(html, "RPG Refugeグラフィック素材")
        self.assertEqual([item["title"] for item in items], ["Actual resource"])

    def test_challenge_page_raises_diagnostic_error(self):
        challenge = """<!DOCTYPE html><html><head>
        <title>Just a moment...</title></head><body>
        <meta http-equiv="refresh" content="0; url=/.stile/challenge">
        </body></html>"""
        with self.assertRaisesRegex(ValueError, "Could not find RPG Refuge thread listings"):
            source.parse_forum_page(challenge, "RPG Refugeグラフィック素材")

    def test_first_run_baselines_without_reporting_old_topics(self):
        html = forum_page(thread_row("A useful plugin", "useful-plugin", 456))
        with patch.object(source, "get_html", return_value=html):
            with patch.object(
                source,
                "FORUM_CATEGORIES",
                (("https://rpg-refuge.com/forums/test.99/", "RPG Refugeプラグイン"),),
            ):
                items, new_seen = source.get_items([])

        self.assertEqual(items, [])
        self.assertEqual(new_seen, ["https://rpg-refuge.com/threads/useful-plugin.456"])

    def test_reports_only_unseen_topics_after_baseline(self):
        old_url = "https://rpg-refuge.com/threads/old-resource.457"
        html = forum_page("".join([
            thread_row("Old resource", "old-resource", 457),
            thread_row("New resource", "new-resource", 458),
        ]))
        with patch.object(source, "get_html", return_value=html):
            with patch.object(
                source,
                "FORUM_CATEGORIES",
                (("https://rpg-refuge.com/forums/test.99/", "RPG Refugeプラグイン"),),
            ):
                items, new_seen = source.get_items([old_url])

        self.assertEqual([item["title"] for item in items], ["New resource"])
        self.assertIn("https://rpg-refuge.com/threads/new-resource.458", new_seen)
        self.assertIn(old_url, new_seen)

    def test_page_fetch_failure_is_not_swallowed(self):
        with patch.object(source, "get_html", side_effect=OSError("network down")):
            with self.assertRaises(OSError):
                source.get_items([])


if __name__ == "__main__":
    unittest.main()
