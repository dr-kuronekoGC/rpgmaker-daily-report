import unittest

from report import build_report


class ReportLanguageDetectionTests(unittest.TestCase):
    def test_build_report_infers_language_for_items_without_language(self):
        item = {
            "title": "テスト用プラグイン",
            "url": "https://example.com/plugin",
            "source": "Test Source",
            "category": "プラグイン",
        }

        report = build_report([item])

        self.assertEqual(item.get("language"), "日本語")
        self.assertIn("Test Source｜日本語", report)


if __name__ == "__main__":
    unittest.main()
