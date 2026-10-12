import unittest
from unittest.mock import Mock, patch

import requests

from sources import official_source_check as source_check


class TestSourceCheckHeaderFallback(unittest.TestCase):
    def test_header_signature_uses_etag_and_last_modified(self):
        response = Mock()
        response.url = "https://example.test/page"
        response.headers = {
            "ETag": '"version-2"',
            "Last-Modified": "Mon, 12 Oct 2026 10:00:00 GMT",
            "Content-Length": "1234",
        }

        with patch.object(source_check.requests, "head", return_value=response) as head:
            signature = source_check.get_header_signature("https://example.test/page")

        self.assertEqual(len(signature), 64)
        head.assert_called_once()

    def test_header_signature_requires_a_validator(self):
        response = Mock()
        response.url = "https://example.test/page"
        response.headers = {"Content-Length": "1234"}

        with patch.object(source_check.requests, "head", return_value=response):
            with self.assertRaisesRegex(ValueError, "no ETag or Last-Modified"):
                source_check.get_header_signature("https://example.test/page")

    def test_http_error_uses_header_fallback_and_detects_change(self):
        site = {
            "name": "GameDevMarket",
            "url": "https://example.test/assets",
            "resource_types": ["グラフィック素材"],
            "language": "英語",
            "site_type": "マーケットプレイス",
        }
        previous = {
            "GameDevMarket": {
                "url": site["url"],
                "signature": "old-signature",
                "method": "headers",
            }
        }

        with patch.object(source_check, "SOURCE_CHECK_SITES", [site]), patch.object(
            source_check, "get_page", side_effect=requests.HTTPError("403 Forbidden")
        ), patch.object(
            source_check, "get_header_signature", return_value="new-signature"
        ) as header_signature:
            items, new_seen = source_check.get_items(previous)

        header_signature.assert_called_once_with(site["url"])
        self.assertEqual(len(items), 1)
        self.assertIn("ページ変化あり（要確認）", items[0]["title"])
        self.assertEqual(new_seen["GameDevMarket"]["method"], "headers")
        self.assertEqual(new_seen["GameDevMarket"]["signature"], "new-signature")

    def test_source_check_uses_separate_connect_and_read_timeouts(self):
        response = Mock()
        response.text = "<html><body>sample content</body></html>"
        with patch.object(source_check.requests, "get", return_value=response) as get:
            source_check.get_page("https://example.test/page")

        self.assertEqual(get.call_args.kwargs["timeout"], (10, 20))

    def test_connection_error_is_retried_once(self):
        response = Mock()
        with patch.object(
            source_check.requests,
            "get",
            side_effect=[requests.exceptions.SSLError("temporary TLS error"), response],
        ) as get:
            with patch.object(source_check.time, "sleep") as sleep:
                result = source_check.request_with_retry("get", "https://example.test", timeout=1)

        self.assertIs(result, response)
        self.assertEqual(get.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_http_status_errors_are_not_retried(self):
        error = requests.HTTPError("403 Forbidden")
        with patch.object(source_check.requests, "get", side_effect=error) as get:
            with self.assertRaises(requests.HTTPError):
                source_check.request_with_retry("get", "https://example.test", timeout=1)

        get.assert_called_once()

    def test_rss_fallback_accepts_valid_feed(self):
        site = {
            "name": "RPG Refuge（2D素材フォーラム）",
            "url": "https://example.test/forums/assets/",
            "alternate_feed_url": "https://example.test/forums/assets/index.rss",
            "resource_types": ["グラフィック素材"],
        }
        previous = {
            site["name"]: {
                "url": site["url"],
                "signature": "old-signature",
                "method": "rss",
            }
        }

        with patch.object(source_check, "SOURCE_CHECK_SITES", [site]), patch.object(
            source_check, "get_page",
            side_effect=source_check.AccessChallengeError("challenge"),
        ), patch.object(
            source_check, "get_rss_signature", return_value="new-signature"
        ) as rss_signature:
            items, new_seen = source_check.get_items(previous)

        rss_signature.assert_called_once_with(
            site["alternate_feed_url"], site["url"]
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(new_seen[site["name"]]["method"], "rss")

    def test_rss_fallback_failure_does_not_use_headers_after_challenge(self):
        site = {
            "name": "RPG Refuge（2D素材フォーラム）",
            "url": "https://example.test/forums/assets/",
            "alternate_feed_url": "https://example.test/forums/assets/index.rss",
        }

        with patch.object(source_check, "SOURCE_CHECK_SITES", [site]), patch.object(
            source_check, "get_page",
            side_effect=source_check.AccessChallengeError("challenge"),
        ), patch.object(
            source_check, "get_rss_signature",
            side_effect=ValueError("not a feed"),
        ), patch.object(source_check, "get_header_signature") as header_signature:
            items, new_seen = source_check.get_items({})

        header_signature.assert_not_called()
        self.assertEqual(items, [])
        self.assertEqual(source_check.LAST_RUN_SUMMARY["failed"], 1)

    def test_access_challenge_does_not_trigger_header_fallback(self):
        site = {
            "name": "RPG Refuge（2D素材フォーラム）",
            "url": "https://example.test/forum",
        }

        with patch.object(source_check, "SOURCE_CHECK_SITES", [site]), patch.object(
            source_check,
            "get_page",
            side_effect=source_check.AccessChallengeError("challenge"),
        ), patch.object(source_check, "get_header_signature") as header_signature:
            items, new_seen = source_check.get_items({})

        header_signature.assert_not_called()
        self.assertEqual(items, [])
        self.assertEqual(new_seen, {})
        self.assertEqual(source_check.LAST_RUN_SUMMARY["failed"], 1)


if __name__ == "__main__":
    unittest.main()
