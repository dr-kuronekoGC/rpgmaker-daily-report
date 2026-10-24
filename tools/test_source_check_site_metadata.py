import unittest

from config import SOURCE_CHECK_SITES
from main import assign_language_if_missing
from report import format_reference_sites


class TestSourceCheckSiteMetadata(unittest.TestCase):
    def test_explicit_site_language_is_not_overwritten_by_generated_japanese_title(self):
        item = {
            "source": "Source Check",
            "category": "SourceCheck",
            "title": "Sang Hendrix：ページ変化あり（要確認）",
            "language": "英語中心（日本語対応プラグインあり）",
        }

        assign_language_if_missing(item)

        self.assertEqual(
            item["language"],
            "英語中心（日本語対応プラグインあり）",
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

    def test_new_rpg_project_has_public_feed_fallback(self):
        site = next(
            site for site in SOURCE_CHECK_SITES
            if site.get("name") == "New RPG Project"
        )
        self.assertEqual(
            site.get("alternate_feed_url"),
            "https://newrpg.seesaa.net/index.rdf",
        )

    def test_inaccessible_sites_are_explicitly_manual_only(self):
        manual_only_names = {
            "GameDevMarket",
            "Maker Devs",
            "RPG Refuge（2D素材フォーラム）",
            "New RPG Project",
        }
        for site in SOURCE_CHECK_SITES:
            if site.get("name") in manual_only_names:
                with self.subTest(site=site["name"]):
                    self.assertIs(site.get("monitoring_enabled"), False)
                    self.assertTrue(site.get("monitoring_note"))

    def test_hendrix_metadata_includes_japanese_plugin_support(self):
        site = next(
            site for site in SOURCE_CHECK_SITES
            if site.get("name") == "Sang Hendrix"
        )
        self.assertIn("日本語", site["language"])

    def test_reference_links_use_clear_heading_and_show_metadata(self):
        lines = format_reference_sites()
        output = "\n".join(lines)

        self.assertIn("【📚 素材・プラグイン関連サイト一覧】", output)
        self.assertIn("対象：", output)
        self.assertIn("主な言語：", output)
        self.assertIn("サイト種別：", output)
        self.assertIn("GameDevMarket", output)
        self.assertIn("Maker Devs", output)
        self.assertIn("RPG Refuge", output)
        self.assertIn("New RPG Project", output)
        self.assertIn("ページ変化を検知できたサイト", output)
        self.assertIn("自動監視：保留", output)


if __name__ == "__main__":
    unittest.main()
