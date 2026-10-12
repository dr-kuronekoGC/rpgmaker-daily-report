import unittest

from sources import community_guild as source


class GuildBodyClassificationTests(unittest.TestCase):
    def test_plugin_description_is_not_misread_as_game(self):
        self.assertIsNone(source.classify_material_content("[MZ] Plugin", ["mz"], "A plugin for RPG Maker MZ. Download it from the store. $14.99 on itch."))

    def test_question_is_detected(self):
        self.assertEqual(source.classify_material_content("Where can I find tilesets?", [], ""), "質問")

    def test_game_showcase_is_detected(self):
        self.assertEqual(source.classify_material_content("My game is out", [], "Here is a gameplay video of my game."), "ゲーム")


if __name__ == "__main__":
    unittest.main()
