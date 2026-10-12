import unittest

from sources import community_guild as source
from classification_scoring import classify_taxonomy_with_evidence


class GuildBodyClassificationTests(unittest.TestCase):
    def test_plugin_description_is_not_misread_as_game(self):
        self.assertIsNone(source.classify_material_content("[MZ] Plugin", ["mz"], "A plugin for RPG Maker MZ. Download it from the store. $14.99 on itch."))

    def test_question_is_detected(self):
        self.assertEqual(source.classify_material_content("Where can I find tilesets?", [], ""), "質問")

    def test_game_showcase_is_detected(self):
        self.assertEqual(source.classify_material_content("My game is out", [], "Here is a gameplay video of my game."), "ゲーム")


    def test_body_text_contributes_to_graphic_taxonomy(self):
        result = classify_taxonomy_with_evidence(
            {
                "title": "New asset",
                "body_text": "A character sprite sheet for RPG Maker.",
            },
            "graphic",
        )
        self.assertGreater(result["classification_scores"]["character"], 0)
        self.assertTrue(
            any(
                entry.get("field") == "body_text"
                for entry in result["classification_evidence"]
            )
        )


if __name__ == "__main__":
    unittest.main()
