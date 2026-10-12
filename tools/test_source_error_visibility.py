import unittest
from unittest.mock import patch

import requests

from sources import community_tsukumate
from sources import official_makerdevs


class TestSourceErrorVisibility(unittest.TestCase):
    def test_maker_devs_ssl_error_propagates(self):
        error = requests.exceptions.SSLError("TLS handshake failed")

        with patch(
            "sources.official_makerdevs.requests.get",
            side_effect=error,
        ), patch(
            "sources.official_makerdevs.log_tls_diagnostics",
        ) as diagnostics:
            with self.assertRaises(requests.exceptions.SSLError):
                official_makerdevs.get_items([])

        diagnostics.assert_called_once_with(
            official_makerdevs.MAKER_DEVS_URL
        )

    def test_tsukumate_connection_error_propagates(self):
        error = requests.exceptions.ConnectTimeout("connection timed out")

        with patch(
            "sources.community_tsukumate.get_mz_forums",
            side_effect=error,
        ):
            with self.assertRaises(requests.exceptions.ConnectTimeout):
                community_tsukumate.get_items(["existing-topic"])

    def test_tsukumate_missing_forums_is_not_reported_as_success(self):
        with patch(
            "sources.community_tsukumate.get_mz_forums",
            return_value={},
        ):
            with self.assertRaisesRegex(RuntimeError, "対象フォーラムを検出できません"):
                community_tsukumate.get_items(["existing-topic"])


if __name__ == "__main__":
    unittest.main()
