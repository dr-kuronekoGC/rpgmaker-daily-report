import unittest

from report import (
    build_report,
    format_reference_sites,
    format_source_check_metadata,
)


class TestManualCheckSitesReport(unittest.TestCase):
    def test_reference_site_listing_includes_type_language_and_format(self):
        sites = [
            {
                "name": "Example Forum",
                "url": "https://example.test/forum",
                "resource_types": ["グラフィック素材", "サウンド素材"],
                "language": "英語",
                "site_type": "掲示板・コミュニティ",
                "reference_only": True,
            },
            {
                "name": "Not Listed",
                "url": "https://example.test/auto",
                "reference_only": False,
            },
        ]

        lines = format_reference_sites(sites)
        text = "\n".join(lines)

        self.assertIn("【📚 参考サイト（個別素材の自動収集対象外）】", text)
        self.assertIn("<https://example.test/forum|Example Forum>", text)
        self.assertIn("対象：グラフィック素材・サウンド素材", text)
        self.assertIn("主な言語：英語", text)
        self.assertIn("サイト種別：掲示板・コミュニティ", text)
        self.assertNotIn("Not Listed", text)
        self.assertIn("ページ変化を検知できたサイト", text)

    def test_page_change_metadata_can_be_formatted(self):
        text = format_source_check_metadata({
            "resource_types": ["プラグイン"],
            "language": "英語",
            "site_type": "プラグイン一覧",
        })

        self.assertEqual(
            text,
            "対象：プラグイン / 主な言語：英語 / サイト種別：プラグイン一覧",
        )

    def test_source_check_does_not_infer_language_from_generated_title(self):
        report = build_report(
            [
                {
                    "title": "Example Site：ページ変化あり（要確認）",
                    "url": "https://example.test/",
                    "category": "SourceCheck",
                    "source": "Source Check",
                    "resource_types": ["プラグイン"],
                    "site_type": "プラグイン配布サイト",
                }
            ],
            source_results=[],
        )

        self.assertIn("対象：プラグイン", report)
        self.assertIn("サイト種別：プラグイン配布サイト", report)
        self.assertNotIn("主な言語：日本語", report)

    def test_no_reference_sites_produces_no_section(self):
        self.assertEqual(format_reference_sites([]), [])


if __name__ == "__main__":
    unittest.main()
