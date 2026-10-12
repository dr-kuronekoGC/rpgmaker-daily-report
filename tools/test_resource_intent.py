import unittest

from asset_metadata import (
    ASSET_TYPE_OTHER,
    ASSET_TYPE_PLUGIN,
    ASSET_TYPE_GRAPHIC,
    build_asset_metadata,
    classify_resource_intent,
    detect_engine,
)
from review_queue import prepare_classification_reviews


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

    def test_release_evidence_in_body_is_not_blocked_by_question_title(self):
        item = build_asset_metadata({
            "title": "How do I use this plugin?",
            "category": "discussion",
            "body_text": "The plugin is released; download here.",
            "url": "https://example.com/plugin",
        })
        self.assertEqual(item["resource_intent"], "resource_candidate")

    def test_insufficient_evidence_stays_uncertain(self):
        intent, confidence, evidence = classify_resource_intent({
            "title": "Interesting post",
            "url": "https://example.com/post",
        })
        self.assertEqual(intent, "uncertain")
        self.assertEqual(confidence, "unknown")
        self.assertEqual(evidence, [])

    def test_clear_resource_candidate_does_not_enter_human_queue(self):
        queue = {"version": 1, "next_pre_number": 1, "items": []}
        item = {
            "internal_id": "ITEM-candidate",
            "title": "Tileset pack",
            "url": "https://example.com/tileset",
            "resource_intent": "resource_candidate",
            "classification_status": "needs_review",
        }
        self.assertEqual(prepare_classification_reviews([item], queue), [])
        self.assertEqual(queue["items"], [])

    def test_uncertain_item_with_resource_evidence_enters_human_queue(self):
        queue = {"version": 1, "next_pre_number": 1, "items": []}
        item = {
            "internal_id": "ITEM-uncertain",
            "title": "Something",
            "url": "https://example.com/post",
            "resource_intent": "uncertain",
            "resource_intent_evidence": [
                {"field": "source_tags_or_tags", "signal": "plugin"}
            ],
            "classification_status": "not_applicable",
        }
        reviews = prepare_classification_reviews([item], queue)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(queue["items"][0]["status"], "open")

    def test_uncertain_item_without_evidence_still_enters_human_queue(self):
        queue = {"version": 1, "next_pre_number": 1, "items": []}
        item = {
            "internal_id": "ITEM-uncertain-empty",
            "title": "Unknown item",
            "url": "https://example.com/unknown",
            "resource_intent": "uncertain",
            "resource_intent_evidence": [],
            "classification_status": "not_applicable",
        }
        reviews = prepare_classification_reviews([item], queue)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(queue["items"][0]["status"], "open")

    def test_legacy_items_keep_existing_review_behavior(self):
        queue = {"version": 1, "next_pre_number": 1, "items": []}
        item = {
            "internal_id": "ITEM-legacy",
            "title": "Legacy item",
            "url": "https://example.com/legacy",
            "classification_status": "needs_review",
        }
        reviews = prepare_classification_reviews([item], queue)
        self.assertEqual(len(reviews), 1)

    def test_engine_aliases_in_titles_are_detected(self):
        cases = [
            ("[RMXP] Fantasy tileset", "XP"),
            ("[VXA] Battle system", "VX Ace"),
            ("[RMMV] Character pack", "MV"),
            ("[RMMZ] Plugin", "MZ"),
            ("[RM2K3] Sound pack", "2003"),
            ("[RM2K] Tileset", "2000"),
            ("[XP/VX/VXA] Resource pack", "XP"),
            ("[XP/VX/VXA] Resource pack", "VX"),
            ("[XP/VX/VXA] Resource pack", "VX Ace"),
        ]
        for title, expected in cases:
            with self.subTest(title=title):
                self.assertIn(expected, detect_engine({"title": title}))

    def test_github_mz_branch_overrides_mv_repository_name(self):
        engines = detect_engine({
            "title": "AccumulateState",
            "url": "https://github.com/triacontane/RPGMakerMV/blob/mz_master/AccumulateState.js",
        })
        self.assertIn("MZ", engines)
        self.assertNotIn("MV", engines)

    def test_github_mv_branch_is_detected(self):
        engines = detect_engine({
            "title": "AccumulateState",
            "url": "https://github.com/triacontane/RPGMakerMV/blob/mv_master/AccumulateState.js",
        })
        self.assertIn("MV", engines)
        self.assertNotIn("MZ", engines)

    def test_compact_engine_names_in_source_tags_are_detected(self):
        cases = [
            ("rpgmakerxp", "XP"),
            ("rpgmakervxa", "VX Ace"),
            ("rpgmakervxace", "VX Ace"),
            ("rpgmakermv", "MV"),
            ("rpgmakermz", "MZ"),
            ("rpgmaker2000", "2000"),
            ("rpgmaker2003", "2003"),
        ]
        for tag, expected in cases:
            with self.subTest(tag=tag):
                self.assertIn(expected, detect_engine({"title": "Resource pack", "source_tags": [tag]}))

    def test_engine_aliases_do_not_match_unrelated_words(self):
        self.assertEqual(detect_engine({"title": "United Kingdom concept art"}), ["汎用"])
        self.assertEqual(detect_engine({"title": "A simple project for XP users"}), ["不明"])

    def test_engine_is_detected_from_body_text(self):
        engines = detect_engine({
            "title": "Tileset pack",
            "body_text": "Made for RPG Maker XP and RPG Maker 2000.",
        })
        self.assertIn("XP", engines)
        self.assertIn("2000", engines)


if __name__ == "__main__":
    unittest.main()
