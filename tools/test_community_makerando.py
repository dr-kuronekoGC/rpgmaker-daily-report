import unittest

from sources.community_makerando import classify, normalize_url


class MakerandoTests(unittest.TestCase):
    def test_accepts_makerando_topic_urls(self):
        self.assertEqual(
            normalize_url("https://www.makerando.com/forum/topic/1282-sample/"),
            "https://www.makerando.com/forum/topic/1282-sample/",
        )
        self.assertIsNone(
            normalize_url("https://example.com/forum/topic/1282-sample/")
        )

    def test_classifies_assets_and_skips_requests(self):
        self.assertEqual(
            classify("Tileset fantasy"),
            "Makerando ITグラフィック素材",
        )
        self.assertEqual(
            classify("Musica battle"),
            "Makerando ITサウンド素材",
        )
        self.assertEqual(
            classify("Plugin per MZ"),
            "Makerando ITプラグイン",
        )
        self.assertIsNone(classify("Richiesta plugin per il menu"))


if __name__ == "__main__":
    unittest.main()
