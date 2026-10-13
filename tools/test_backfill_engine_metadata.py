import unittest
from tools.backfill_engine_metadata import propose_engine_update, transform_archive_data


class EngineBackfillPreviewTests(unittest.TestCase):
    def test_placeholder_is_replaced(self):
        item = {"title": "[RMXP] Fantasy tileset", "engine": ["不明"]}
        self.assertEqual(propose_engine_update(item), ["XP"])
        self.assertEqual(item["engine"], ["不明"])

    def test_explicit_multi_engine_title_does_not_change_existing_specific_engine(self):
        item = {"title": "[XP/VX/VXA] Resource pack", "engine": ["XP"]}
        self.assertIsNone(propose_engine_update(item))

    def test_placeholder_with_explicit_multi_engine_title_adds_engines(self):
        item = {"title": "[XP/VX/VXA] Resource pack", "engine": ["不明"]}
        self.assertEqual(set(propose_engine_update(item)), {"XP", "VX", "VX Ace"})

    def test_no_evidence_is_noop(self):
        self.assertIsNone(propose_engine_update({"title": "Generic icon pack", "engine": ["不明"]}))

    def test_already_present_engine_is_noop(self):
        self.assertIsNone(propose_engine_update({"title": "[RMXP] Tileset", "engine": ["XP"]}))

    def test_conflicting_specific_engine_is_noop(self):
        item = {"title": "A generic forest resource", "engine": ["MV"], "source_tags": ["rpgmakermz"]}
        self.assertIsNone(propose_engine_update(item))

    def test_placeholder_cleanup_preserves_unrelated_labels(self):
        item = {"title": "[RMMZ] Icon pack", "engine": ["その他RPG Maker", "不明", "汎用"]}
        self.assertEqual(propose_engine_update(item), ["汎用", "MZ"])

    def test_archive_transform_keeps_original_and_reports_conflicts(self):
        original = {"items": [
            {"title": "[RMMV] Icon set", "engine": ["不明"], "other": 7},
            {"title": "General assets", "engine": ["不明"], "other": 8},
            {"title": "A generic forest resource", "engine": ["MV"], "source_tags": ["rpgmakermz"]},
        ], "metadata": {"keep": True}}
        transformed, changes, conflicts = transform_archive_data(original, "2026-10.json")
        self.assertEqual(len(changes), 1)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(original["items"][0]["engine"], ["不明"])
        self.assertEqual(transformed["items"][0]["engine"], ["MV"])
        self.assertEqual(transformed["items"][0]["other"], 7)
        self.assertEqual(transformed["items"][1], original["items"][1])
        self.assertEqual(transformed["items"][2]["engine"], ["MV"])
        self.assertEqual(transformed["metadata"], original["metadata"])

    def test_top_level_list_is_supported(self):
        transformed, changes, conflicts = transform_archive_data([
            {"title": "[RMMZ] Tileset", "engine": ["その他RPG Maker"]}
        ])
        self.assertEqual(transformed[0]["engine"], ["MZ"])
        self.assertEqual(len(changes), 1)
        self.assertEqual(conflicts, [])

    def test_unexpected_shape_is_rejected(self):
        with self.assertRaises(ValueError):
            transform_archive_data({"records": []})


if __name__ == "__main__":
    unittest.main()
