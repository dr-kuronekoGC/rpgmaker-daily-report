import unittest

from report import (
    format_manual_check_sites,
    format_source_check_metadata,
)


class TestManualCheckSitesReport(unittest.TestCase):
    def test_manual_site_listing_includes_type_language_and_format(self):
        sites = [
            {
                "name": "Example Forum",
                "url": "https://example.test/forum",
                "resource_types": ["グラフィック素材", "サウンド素材"],
                "language": "英語",
                "site_type": "掲示板・コミュニティ",
                "manual_review": True,
            },
            {
                "name": "Not Listed",
                "url": "https://example.test/auto",
                "manual_review": False,
            },
        ]

        lines = format_manual_check_sites(sites)
        text = "\n".join(lines)

        self.assertIn("【🔎 要チェックサイト】", text)
        self.assertIn("<https://example.test/forum|Example Forum>", text)
        self.assertIn("対象：グラフィック素材・サウンド素材", text)
        self.assertIn("言語：英語", text)
        self.assertIn("形式：掲示板・コミュニティ", text)
        self.assertNotIn("Not Listed", text)

    def test_page_change_metadata_can_be_formatted(self):
        text = format_source_check_metadata({
            "resource_types": ["プラグイン"],
            "language": "英語",
            "site_type": "プラグイン一覧",
        })

        self.assertEqual(
            text,
            "対象：プラグイン / 言語：英語 / 形式：プラグイン一覧",
        )

    def test_no_manual_sites_produces_no_section(self):
        self.assertEqual(format_manual_check_sites([]), [])


if __name__ == "__main__":
    unittest.main()
