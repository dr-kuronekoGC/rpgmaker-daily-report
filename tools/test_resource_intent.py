import unittest

from asset_metadata import (
    ASSET_TYPE_OTHER,
    ASSET_TYPE_PLUGIN,
    ASSET_TYPE_GRAPHIC,
    build_asset_metadata,
    classify_resource_intent,
    detect_engine,
)


class ResourceIntentTests(unittest.TestCase):
    def test_clear_question_in_plugin_section_is_not_a_plugin_release(self):
        item = build_asset_metadata({
            "title": "How do I add a particle effect?",
            "category": "plugin",
            "url": "https://example.com/topic",
        })
        self.assertEqual(item["resource_intent"], "not_resource")
        self.assertEqual(item["asset_type"], ASSET_TYPE_OTHER)

    def test_clear_showcase_is_not_a_resource(self):
        item = build_asset_metadata({
            "title": "Gameplay video of my game",
            "category": "Redditグラフィック素材",
            "url": "https://example.com/showcase",
        })
        self.assertEqual(item["resource_intent"], "not_resource")
        self.assertEqual(item["asset_type"], ASSET_TYPE_OTHER)

    def test_concrete_distribution_signal_overrides_question_context(self):
        item = {
            "title": "How do I use this plugin?",
            "category": "discussion",
            "body_text": "The plugin is released; download here.",
            "url": "https://example.com/plugin",
        }
        intent, confidence, evidence = classify_resource_intent(item)
        self.assertEqual(intent, "resource_candidate")
        self.assertTrue(evidence)

    def test_paid_tileset_remains_a_resource_candidate(self):
        item = build_asset_metadata({
            "title": "Premium tileset pack",
            "description": "Paid download for RPG Maker XP.",
            "price_status": "paid",
            "url": "https://example.com/tileset",
        })
        self.assertEqual(item["resource_intent"], "resource_candidate")
        self.assertEqual(item["asset_type"], ASSET_TYPE_GRAPHIC)

    def test_insufficient_evidence_stays_uncertain(self):
        intent, confidence, evidence = classify_resource_intent({
            "title": "Interesting post",
            "url": "https://example.com/post",
        })
        self.assertEqual(intent, "uncertain")
        self.assertEqual(confidence, "unknown")
        self.assertEqual(evidence, [])

    def test_engine_is_detected_from_body_text(self):
        engines = detect_engine({
            "title": "Tileset pack",
            "body_text": "Made for RPG Maker XP and RPG Maker 2000.",
        })
        self.assertIn("XP", engines)
        self.assertIn("2000", engines)


if __name__ == "__main__":
    unittest.main()
