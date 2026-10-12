import unittest

from asset_metadata import _is_non_asset_title


class ResourceIntentGuardTests(unittest.TestCase):
    def test_engine_in_plugin_title_is_not_a_non_asset_signal(self):
        self.assertFalse(
            _is_non_asset_title("RPG Maker MZ - Gun & Zombie ABS Engine Pro")
        )

    def test_generic_video_word_is_not_a_non_asset_signal(self):
        self.assertFalse(
            _is_non_asset_title("Official plugin video and download")
        )

    def test_explicit_gameplay_video_remains_a_non_asset_signal(self):
        self.assertTrue(
            _is_non_asset_title("Gameplay video of my game")
        )

    def test_question_title_remains_a_non_asset_signal(self):
        self.assertTrue(
            _is_non_asset_title("How do I add a particle effect?")
        )


if __name__ == "__main__":
    unittest.main()
