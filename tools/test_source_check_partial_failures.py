import unittest
from unittest.mock import patch

import requests

from sources import official_source_check


class TestSourceCheckPartialFailures(unittest.TestCase):
    def setUp(self):
        self.sites = [
            {"name": "Working Site", "url": "https://example.test/working"},
            {"name": "Timed Out Site", "url": "https://example.test/timeout"},
            {"name": "Baseline Site", "url": "https://example.test/baseline"},
        ]

    def test_partial_failure_is_counted_and_failed_signature_is_preserved(self):
        old_signature = "old-signature"
        seen = {
            "Working Site": {
                "url": self.sites[0]["url"],
                "signature": old_signature,
            },
            "Timed Out Site": {
                "url": self.sites[1]["url"],
                "signature": "must-stay",
            },
        }

        def fake_get_page(url):
            if url == self.sites[1]["url"]:
                raise requests.exceptions.ReadTimeout("timed out")
            return "<html><body><a href='/new'>New resource</a></body></html>"

        with patch.object(official_source_check, "SOURCE_CHECK_SITES", self.sites), patch.object(
            official_source_check, "get_page", side_effect=fake_get_page
        ):
            items, new_seen = official_source_check.get_items(seen)

        self.assertEqual(official_source_check.LAST_RUN_SUMMARY["checked"], 2)
        self.assertEqual(official_source_check.LAST_RUN_SUMMARY["updated"], 1)
        self.assertEqual(official_source_check.LAST_RUN_SUMMARY["baseline"], 1)
        self.assertEqual(official_source_check.LAST_RUN_SUMMARY["failed"], 1)
        self.assertEqual(
            new_seen["Timed Out Site"]["signature"],
            "must-stay",
        )
        self.assertNotEqual(
            new_seen["Working Site"]["signature"],
            old_signature,
        )
        self.assertIn("Working Site：更新あり", [item["title"] for item in items])
        self.assertIn("Baseline Site", new_seen)

    def test_all_successful_sites_are_reported_as_complete(self):
        with patch.object(official_source_check, "SOURCE_CHECK_SITES", self.sites[:1]), patch.object(
            official_source_check,
            "get_page",
            return_value="<html><body><a href='/resource'>Resource page</a></body></html>",
        ):
            _, _ = official_source_check.get_items({})

        self.assertEqual(official_source_check.LAST_RUN_SUMMARY["failed"], 0)
        self.assertEqual(official_source_check.LAST_RUN_SUMMARY["checked"], 1)


if __name__ == "__main__":
    unittest.main()
