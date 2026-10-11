import unittest

from classification_scoring import classify_sound_with_evidence


class ClassificationScoringTests(unittest.TestCase):
    def test_explicit_bgm_keeps_high_confidence(self):
        result = classify_sound_with_evidence({
            "title": "Fantasy BGM Pack",
            "description": "Background music for an RPG Maker game",
        })
        self.assertEqual(result["sound_type"], "BGM")
        self.assertEqual(result["classification_confidence"], "high")
        self.assertEqual(result["classification_status"], "auto")

    def test_unrelated_item_does_not_force_a_sound_type(self):
        result = classify_sound_with_evidence({
            "title": "A tileset for a forest village",
            "description": "Graphic assets for RPG Maker",
        })
        self.assertIsNone(result["sound_type"])
        self.assertEqual(result["classification_confidence"], "unknown")
        self.assertEqual(result["classification_status"], "needs_review")


if __name__ == "__main__":
    unittest.main()
