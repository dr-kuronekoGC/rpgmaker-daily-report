import unittest

from sources.community_rmplanet import classify


class RMPlanetTests(unittest.TestCase):
    def test_classifies_reusable_resources(self):
        self.assertEqual(
            classify("Free MZ tileset pack"),
            "RM Planetグラフィック素材",
        )
        self.assertEqual(
            classify("New battle music and sound effects"),
            "RM Planetサウンド素材",
        )
        self.assertEqual(
            classify("Plugin: Better battle animations"),
            "RM Planetプラグイン",
        )

    def test_skips_questions_and_general_topics(self):
        self.assertIsNone(classify("Help: looking for a tileset"))
        self.assertIsNone(classify("What did you work on today?"))


if __name__ == "__main__":
    unittest.main()
