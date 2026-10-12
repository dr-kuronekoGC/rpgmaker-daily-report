import unittest

from report import format_source_health_warnings


class TestSourceHealthWarnings(unittest.TestCase):
    def test_successful_collectors_are_omitted(self):
        self.assertEqual(
            format_source_health_warnings([
                {"name": "community_reddit", "status": "OK"},
            ]),
            [],
        )

    def test_partial_and_failed_collectors_are_reported(self):
        lines = format_source_health_warnings([
            {
                "name": "official_source_check",
                "status": "PARTIAL",
                "summary": {"checked": 6, "failed": 2},
            },
            {
                "name": "official_gamedevmarket",
                "status": "ERROR",
                "error_type": "HTTPError",
            },
        ])

        self.assertEqual(lines[0], "【⚠️ 収集元の取得状況】")
        self.assertIn(
            "official_source_check：一部失敗 （確認 6/8、失敗 2件）",
            lines,
        )
        self.assertIn(
            "official_gamedevmarket：取得失敗（HTTPError）",
            lines,
        )

    def test_empty_results_do_not_add_warning(self):
        self.assertEqual(format_source_health_warnings([]), [])


if __name__ == "__main__":
    unittest.main()
