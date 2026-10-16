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

    def test_forum_asset_request_titles_are_non_assets(self):
        titles = [
            "Need Char Sets and Battlers",
            "PLUGIN REQUEST: Limited inventory that is compatible with SRPG MV",
            "Need a BGS",
            "Looking for a tileset pack",
            "Cerco charsets per RPG Maker",
            "Mi serve un plugin per il menu",
            "探しています：キャラクター素材",
        ]
        for title in titles:
            with self.subTest(title=title):
                self.assertTrue(_is_non_asset_title(title))

    def test_resource_title_without_request_language_is_not_blocked(self):
        titles = [
            "My new Battler",
            "Battle Sprites",
            "Fantasy tileset pack",
            "RPG Maker MZ - Gun & Zombie ABS Engine Pro",
        ]
        for title in titles:
            with self.subTest(title=title):
                self.assertFalse(_is_non_asset_title(title))


if __name__ == "__main__":
    unittest.main()
