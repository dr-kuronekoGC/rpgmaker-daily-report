import unittest

from sources.community_rpgmaker_es import classify


class SpanishCommunityTests(unittest.TestCase):
    def test_classifies_plugins_and_assets(self):
        self.assertEqual(
            classify("Nuevo plugin para RPG Maker MZ"),
            "Comunidad RPG Maker ESプラグイン",
        )
        self.assertEqual(
            classify("Tileset de bosque para MV", "Recursos Gráficos"),
            "Comunidad RPG Maker ESグラフィック素材",
        )
        self.assertEqual(
            classify("Música de batalla", "Recursos"),
            "Comunidad RPG Maker ESサウンド素材",
        )

    def test_skips_help_requests(self):
        self.assertIsNone(classify("Ayuda: necesito un plugin"))


if __name__ == "__main__":
    unittest.main()
