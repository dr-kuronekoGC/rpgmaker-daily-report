import unittest

from tools.backfill_engine_metadata import propose_engine_update, transform_archive_data


class EngineBackfillPreviewTests(unittest.TestCase):
    def test_replaces_placeholder_with_specific_engine(self):
        item = {"title": "[RMXP] Fantasy tileset", "engine": ["不明"]}
        self.assertEqual(propose_engine_update(item), ["XP"])
        self.assertEqual(item["engine"], ["不明"])

    def test_preserves_existing_engine_and_adds_explicit_second_engine(self):
        item = {"title": "[XP/VX/VXA] Resource pack", "engine": ["XP"]}
        self.assertEqual(set(propose_engine_update(item)), {"XP", "VX", "VX Ace"})

    def test_does_not_change_without_concrete_evidence(self):
        self.assertIsNone(propose_engine_update({"title": "Generic icon pack", "engine": ["不明"]}))

    def test_does_not_change_when_engine_is_already_present(self):
        self.assertIsNone(propose_engine_update({"title": "[RMXP] Tileset", "engine": ["XP"]}))

    def test_conflicting_specific_engine_is_not_overwritten_or_extended(self):
        item = {"title": "Futuristic Outlands | Weird Structures in a Forest",
                "engine": ["MV"], "source_tags": ["rpgmakermz"]}
        self.assertIsNone(propose_engine_update(item))

    def test_preserves_unrelated_engine_labels_and_replaces_placeholders(self):
        item = {"title": "[RMMZ] Icon pack", "engine": ["その他RPG Maker", "不明", "汎用"]}
        self.assertEqual(propose_engine_update(item), ["汎用", "MZ"])

    def test_transform_only_changes_engine_field_and_returns_a_copy(self):
        original = {
            "metadata": {"keep": True},
            "items": [
                {"internal_id": "A", "title": "[RMMV] Icon set", "engine": ["不明"], "other": 7},
                {"internal_id": "B", "title": "General assets", "engine": ["不明"], "other": 8},
                {"internal_id": "C", "title": "Futuristic Outlands | Weird Structures in a Forest",
                 "engine": ["MV"], "source_tags": ["rpgmakermz"]},
            ],
        }
        transformed, changes, conflicts = transform_archive_data(original, "2026-10.json")
        self.assertEqual(len(changes), 1)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(original["items"][0]["engine"], ["不明"])
        self.assertEqual(transformed["items"][0]["engine"], ["MV"])
        self.assertEqual(transformed["items"][0]["other"], 7)
        self.assertEqual(transformed["metadata"], original["metadata"])
        self.assertEqual(transformed["items"][1], original["items"][1])
        self.assertEqual(transformed["items"][2]["engine"], ["MV"])

    def test_supports_top_level_list_archive(self):
        transformed, changes, conflicts = transform_archive_data([
            {"title": "[RMMZ] Tileset", "engine": ["その他RPG Maker"]}
        ])
        self.assertEqual(transformed[0]["engine"], ["MZ"])
        self.assertEqual(len(changes), 1)
        self.assertEqual(conflicts, [])

    def test_rejects_unexpected_archive_shape(self):
        with self.assertRaises(ValueError):
            transform_archive_data({"records": []})


if __name__ == "__main__":
    unittest.main()
