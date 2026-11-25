import unittest
from unittest.mock import patch

import requests

from sources.base import get_html, get_request_stats, reset_request_stats


def response_with_status(status_code):
    response = requests.Response()
    response.status_code = status_code
    response.url = "https://www.rpg-maker.fr/scripts-pour-vxace-type-3.html"
    response._content = b"ok"
    return response


class OniromancieRetryTests(unittest.TestCase):
    def setUp(self):
        reset_request_stats()

    @patch("sources.base.time.sleep")
    @patch("sources.base.requests.get")
    def test_retries_transient_server_errors_then_succeeds(self, mock_get, mock_sleep):
        mock_get.side_effect = [
            response_with_status(500),
            response_with_status(503),
            response_with_status(200),
        ]
        html = get_html(
            "https://www.rpg-maker.fr/scripts-pour-vxace-type-3.html",
            retry_status_codes=(500, 502, 503, 504),
            max_retries=2,
            retry_delay=1,
        )
        self.assertEqual(html, "ok")
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual([call.args[0] for call in mock_sleep.call_args_list], [1, 2])
        self.assertEqual(get_request_stats(), {"succeeded": 1, "failed": 0})

    @patch("sources.base.time.sleep")
    @patch("sources.base.requests.get")
    def test_stops_after_two_retries_and_counts_one_final_failure(self, mock_get, mock_sleep):
        mock_get.side_effect = [
            response_with_status(500),
            response_with_status(502),
            response_with_status(504),
        ]
        with self.assertRaises(requests.HTTPError):
            get_html(
                "https://www.rpg-maker.fr/scripts-pour-vxace-type-3.html",
                retry_status_codes=(500, 502, 503, 504),
                max_retries=2,
                retry_delay=1,
            )
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(get_request_stats(), {"succeeded": 0, "failed": 1})

    @patch("sources.base.time.sleep")
    @patch("sources.base.requests.get")
    def test_does_not_retry_non_transient_status(self, mock_get, mock_sleep):
        mock_get.return_value = response_with_status(404)
        with self.assertRaises(requests.HTTPError):
            get_html(
                "https://www.rpg-maker.fr/scripts-pour-vxace-type-3.html",
                retry_status_codes=(500, 502, 503, 504),
                max_retries=2,
                retry_delay=1,
            )
        mock_get.assert_called_once()
        mock_sleep.assert_not_called()
        self.assertEqual(get_request_stats(), {"succeeded": 0, "failed": 1})


if __name__ == "__main__":
    unittest.main()
