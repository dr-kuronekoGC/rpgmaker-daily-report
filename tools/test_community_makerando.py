import unittest

from sources.community_makerando import (
    classify,
    find_section_urls,
    normalize_url,
)


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
            classify("Musica battle", section_type="sound"),
            "Makerando ITサウンド素材",
        )
        self.assertEqual(
            classify("Battle Animation Pointer", section_type="plugin"),
            "Makerando ITプラグイン",
        )
        self.assertIsNone(
            classify("Richiesta plugin per il menu", section_type="plugin")
        )

    def test_finds_resource_forum_sections_from_labels(self):
        html = """
        <a href="/forum/42-rpg-maker-scripting/">RPG Maker Scripting</a>
        <a href="/forum/55-musica-e-suoni/">Musica e Suoni</a>
        <a href="/forum/71-risorse-grafiche-rpg-maker/">Risorse Grafiche RPG Maker</a>
        """
        self.assertEqual(
            find_section_urls(html),
            {
                "https://www.makerando.com/forum/42-rpg-maker-scripting/": "plugin",
                "https://www.makerando.com/forum/55-musica-e-suoni/": "sound",
                "https://www.makerando.com/forum/71-risorse-grafiche-rpg-maker/": "graphics",
            },
        )


if __name__ == "__main__":
    unittest.main()
