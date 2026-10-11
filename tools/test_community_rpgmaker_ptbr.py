import unittest

from sources.community_rpgmaker_ptbr import classify, normalize_url


class PortugueseCommunityTests(unittest.TestCase):
    def test_accepts_only_forum_threads(self):
        self.assertEqual(
            normalize_url("https://condadobraveheart.com/threads/200x-mz-converter-converta-jogos-antigos-de-rm2k-para-mz.8689/"),
            "https://condadobraveheart.com/threads/200x-mz-converter-converta-jogos-antigos-de-rm2k-para-mz.8689",
        )
        self.assertIsNone(normalize_url("https://example.com/threads/tool.123/"))

    def test_classifies_tools_and_skips_questions(self):
        self.assertEqual(
            classify("200x/MZ Converter - Converta jogos antigos de Rm2k para MZ"),
            "Condado PT-BRツール",
        )
        self.assertIsNone(classify("Alguém tem RPG Maker VX Ace?"))


if __name__ == "__main__":
    unittest.main()
