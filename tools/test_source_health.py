import unittest

from sources.health import determine_source_status


class SourceHealthStatusTests(unittest.TestCase):
    def test_no_failures_is_ok(self):
        self.assertEqual(determine_source_status({"succeeded": 3, "failed": 0}), "OK")

    def test_mixed_requests_are_partial(self):
        self.assertEqual(determine_source_status({"succeeded": 2, "failed": 1}), "PARTIAL")

    def test_all_tracked_requests_failed_is_error(self):
        self.assertEqual(determine_source_status({"succeeded": 0, "failed": 2}), "ERROR")

    def test_collector_summary_can_mark_partial(self):
        self.assertEqual(
            determine_source_status({"succeeded": 0, "failed": 0}, {"failed": 3, "checked": 8}),
            "PARTIAL",
        )


if __name__ == "__main__":
    unittest.main()
