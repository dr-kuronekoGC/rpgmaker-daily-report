import unittest
from unittest.mock import patch

from sources import official_gamedevmarket


class GameDevMarketErrorVisibilityTests(unittest.TestCase):
    def test_http_error_is_propagated_to_source_health(self):
        with patch.object(
            official_gamedevmarket,
            "collect_html",
            side_effect=RuntimeError("403 Client Error: Forbidden"),
        ):
            with self.assertRaisesRegex(RuntimeError, "403 Client Error"):
                official_gamedevmarket.get_items([])


if __name__ == "__main__":
    unittest.main()
