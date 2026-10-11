import unittest

from sources.community_rpgmaker_it import classify, normalize_url


class ItalianCommunityTests(unittest.TestCase):
    def test_accepts_invision_topic_urls(self):
        url = "https://www.rpg2s.it/forum/index.php?/topic/12345-sample-plugin/"
        self.assertEqual(normalize_url(url), url)
        self.assertIsNone(normalize_url("https://example.com/topic/12345-test/"))

    def test_classifies_plugins_and_skips_questions(self):
        self.assertEqual(classify("Il mio Plugin audio manager"), "Rpg2S ITプラグイン")
        self.assertIsNone(classify("Richiesta plugin per il menu"))


if __name__ == "__main__":
    unittest.main()
