import unittest

from config import SOURCE_CHECK_SITES
from main import assign_language_if_missing
from report import format_manual_check_sites


class TestSourceCheckSiteMetadata(unittest.TestCase):
    def test_explicit_site_language_is_not_overwritten_by_generated_japanese_title(self):
        item = {
            "source": "Source Check",
            "category": "SourceCheck",
            "title": "Sang Hendrix：ページ変化あり（要確認）",
            "language": "英語・日本語（一部プラグイン対応）",
        }

        assign_language_if_missing(item)

        self.assertEqual(
            item["language"],
            "英語・日本語（一部プラグイン対応）",
        )

    def test_missing_language_can_still_be_inferred(self):
        item = {"title": "新着プラグインのお知らせ"}

        assign_language_if_missing(item)

        self.assertEqual(item["language"], "日本語")

    def test_all_source_check_sites_have_classification_metadata(self):
        self.assertTrue(SOURCE_CHECK_SITES)

        for site in SOURCE_CHECK_SITES:
            with self.subTest(site=site.get("name")):
                self.assertTrue(site.get("name"))
                self.assertTrue(site.get("url"))
                self.assertTrue(site.get("resource_types"))
                self.assertTrue(site.get("language"))
                self.assertTrue(site.get("site_type"))

    def test_hendrix_metadata_includes_japanese_plugin_support(self):
        site = next(
            site for site in SOURCE_CHECK_SITES
            if site.get("name") == "Sang Hendrix"
        )
        self.assertIn("日本語", site["language"])

    def test_manual_links_use_clear_heading_and_show_metadata(self):
        lines = format_manual_check_sites()
        output = "\n".join(lines)

        self.assertIn("【📌 手動確認リンク】", output)
        self.assertIn("対象：", output)
        self.assertIn("言語：", output)
        self.assertIn("サイト種別：", output)
        self.assertIn("GameDevMarket", output)
        self.assertIn("Maker Devs", output)
        self.assertIn("RPG Refuge", output)


if __name__ == "__main__":
    unittest.main()
