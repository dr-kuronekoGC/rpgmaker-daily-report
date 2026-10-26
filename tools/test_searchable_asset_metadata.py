import unittest

from asset_metadata import build_asset_metadata
from classification_scoring import classify_sound_with_evidence


class SearchableAssetMetadataTests(unittest.TestCase):
    def test_sound_formats_are_detected_and_engine_is_not_relevant(self):
        item = build_asset_metadata({
            "category": "サウンド素材",
            "title": "Forest BGM Pack (.ogg and .mid)",
            "description": "Audio files supplied as OGG and MIDI.",
            "url": "https://example.invalid/resources/forest",
        })
        self.assertEqual(item["asset_type"], "sound")
        self.assertEqual(item["file_formats"], ["mid", "ogg"])
        self.assertFalse(item["engine_relevant"])

    def test_sound_format_is_not_inferred_from_page_url(self):
        item = build_asset_metadata({
            "category": "サウンド素材",
            "title": "Forest ambience",
            "description": "Ambient background sound.",
            "url": "https://example.invalid/downloads/track.ogg",
        })
        self.assertEqual(item["file_formats"], [])
        self.assertFalse(item["engine_relevant"])

    def test_voice_pack_is_a_distinct_sound_type(self):
        result = classify_sound_with_evidence({
            "title": "Japanese Voice Pack",
            "category": "サウンド素材",
        })
        self.assertEqual(result["sound_type"], "VOICE")

    def test_graphic_facets_and_format_are_detected(self):
        item = build_asset_metadata({
            "category": "グラフィック素材",
            "title": "Fantasy Pixel Art Tileset (.png)",
            "description": "A forest village tileset for RPG Maker.",
        })
        self.assertEqual(item["asset_type"], "graphic")
        self.assertIn("png", item["file_formats"])
        self.assertIn("pixel_art", item["graphic_style"])
        self.assertIn("fantasy", item["graphic_theme"])
        self.assertTrue(item["engine_relevant"])

    def test_graphic_metadata_does_not_invent_missing_style(self):
        item = build_asset_metadata({
            "category": "グラフィック素材",
            "title": "Village tileset",
            "description": "A tileset for an RPG Maker game.",
        })
        self.assertEqual(item["graphic_style"], [])
        self.assertEqual(item["graphic_theme"], [])


if __name__ == "__main__":
    unittest.main()
