import unittest

from sources.community_rpgmaker_it import (
    classify,
    find_section_urls,
    normalize_url,
)


class ItalianCommunityTests(unittest.TestCase):
    def test_accepts_invision_topic_urls(self):
        url = "https://www.rpg2s.it/forum/index.php?/topic/12345-sample-plugin/"
        self.assertEqual(normalize_url(url), url)
        self.assertIsNone(normalize_url("https://example.com/topic/12345-test/"))

    def test_classifies_plugins_and_skips_questions(self):
        self.assertEqual(
            classify("Il mio Plugin audio manager"),
            "Rpg2S ITプラグイン",
        )
        self.assertIsNone(classify("Richiesta plugin per il menu"))
        self.assertEqual(
            classify("Battle Animation Pointer", section_type="plugin"),
            "Rpg2S ITプラグイン",
        )

    def test_classifies_graphics_and_sound_topics(self):
        self.assertEqual(
            classify("Tileset fantasy", section_type="graphics"),
            "Rpg2S ITグラフィック素材",
        )
        self.assertEqual(
            classify("Composizione brani", section_type="sound"),
            "Rpg2S ITサウンド素材",
        )
        self.assertIsNone(
            classify("Richiesta risorse sonore", section_type="sound")
        )

    def test_discovers_dedicated_mz_mv_graphics_and_sound_sections(self):
        html = """
        <a href="/forum/index.php?/forum/11-grafica/">Grafica</a>
        <a href="/forum/index.php?/forum/148-donazione-risorse-grafiche-mz/">Donazione risorse grafiche MZ</a>
        <a href="/forum/index.php?/forum/128-donazione-risorse-grafiche-mv/">Donazione risorse grafiche MV</a>
        <a href="/forum/index.php?/forum/18-donazione-risorse-sonore/">Donazione Risorse Sonore</a>
        <a href="/forum/index.php?/forum/150-richiesta-risorse-grafiche-mz/">Richiesta risorse grafiche MZ</a>
        <a href="/forum/index.php?/topic/12345-sample/">Sample topic</a>
        """
        self.assertEqual(
            find_section_urls(html),
            {
                "https://www.rpg2s.it/forum/index.php?/forum/148-donazione-risorse-grafiche-mz/": "graphics",
                "https://www.rpg2s.it/forum/index.php?/forum/149-donazione-risorse-grafiche-mv/": "graphics",
                "https://www.rpg2s.it/forum/index.php?/forum/18-donazione-risorse-sonore/": "sound",
            },
        )


if __name__ == "__main__":
    unittest.main()
