import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from sources.official_visustella import (
    LAST_FETCH_PREFIX,
    MIN_FETCH_INTERVAL,
    _get_last_attempt,
    _should_skip_fetch,
    get_items,
)


class VisuStellaThrottleTests(unittest.TestCase):
    def test_skips_when_last_attempt_was_less_than_24_hours_ago(self):
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
        self.assertFalse(_should_skip_fetch(["https://visustellamz.itch.io/example"]))

    def test_error_records_attempt_timestamp_and_preserves_urls(self):
        seen = ["https://visustellamz.itch.io/old-plugin"]
        with patch(
            "sources.official_visustella.get_html",
            side_effect=RuntimeError("HTTP 429"),
        ):
            items, new_seen = get_items(seen)

        self.assertEqual(items, [])
        self.assertIn("https://visustellamz.itch.io/old-plugin", new_seen)
        self.assertIsNotNone(_get_last_attempt(new_seen))
        self.assertEqual(
            sum(
                isinstance(value, str) and value.startswith(LAST_FETCH_PREFIX)
                for value in new_seen
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()
