import unittest

from report import format_carryover_pre_ids, format_review_summary


class ReviewCarryoverSummaryTests(unittest.TestCase):
    def test_contiguous_ids_are_shown_as_one_range(self):
        items = [{"pre_id": f"PRE-{number:05d}"} for number in range(107, 226)]
        self.assertEqual(
            format_carryover_pre_ids(items),
            "対象ID：PRE-00107〜PRE-00225",
        )

    def test_gaps_are_preserved_in_the_summary(self):
        items = [{"pre_id": value} for value in (
            "PRE-00107", "PRE-00108", "PRE-00110", "PRE-00112"
        )]
        self.assertEqual(
            format_carryover_pre_ids(items),
            "対象ID：PRE-00107〜PRE-00108、PRE-00110、PRE-00112",
        )

    def test_many_ranges_are_truncated_with_remaining_count(self):
        numbers = [107, 109, 111, 113, 115, 117, 119]
        items = [{"pre_id": f"PRE-{number:05d}"} for number in numbers]
        result = format_carryover_pre_ids(items, max_ranges=3)
        self.assertEqual(
            result,
            "対象ID：PRE-00107、PRE-00109、PRE-00111、ほか4件",
        )

    def test_invalid_ids_are_ignored_and_empty_result_is_none(self):
        self.assertIsNone(format_carryover_pre_ids([{"pre_id": "bad"}, {}]))

    def test_slack_summary_stays_compact_for_large_carryover(self):
        items = [{"pre_id": f"PRE-{number:05d}", "created_report_date": "2026-09-22"} for number in range(107, 226)]
        result = format_review_summary([], items)
        self.assertIn("119件", result)
        self.assertIn("PRE-00107〜PRE-00225", result[4])
        self.assertLess(len(result[3]), 60)
        self.assertNotIn("PRE-00108", result[3])


if __name__ == "__main__":
    unittest.main()
