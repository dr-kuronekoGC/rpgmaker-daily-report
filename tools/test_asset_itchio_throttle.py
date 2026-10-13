import unittest
from datetime import datetime, timedelta, timezone

from sources.asset_itchio import (
    LAST_FETCH_PREFIX,
    MIN_FETCH_INTERVAL,
    _get_last_successful_fetch,
    _should_skip_fetch,
)


class ItchIoThrottleTests(unittest.TestCase):
    def test_skips_when_last_successful_check_was_less_than_24_hours_ago(self):
        now = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)
        last_check = now - timedelta(hours=23)
        seen = [LAST_FETCH_PREFIX + last_check.isoformat()]

        self.assertTrue(_should_skip_fetch(seen, now=now))

    def test_allows_check_after_24_hours(self):
        now = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)
        last_check = now - MIN_FETCH_INTERVAL
        seen = [LAST_FETCH_PREFIX + last_check.isoformat()]

        self.assertFalse(_should_skip_fetch(seen, now=now))

    def test_missing_timestamp_allows_first_check(self):
        self.assertFalse(_should_skip_fetch(["https://itch.io/example"]))

    def test_reads_timestamp_marker_without_treating_it_as_a_url(self):
        expected = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
        seen = [
            "https://itch.io/example",
            LAST_FETCH_PREFIX + expected.isoformat(),
        ]

        self.assertEqual(_get_last_successful_fetch(seen), expected)


if __name__ == "__main__":
    unittest.main()
