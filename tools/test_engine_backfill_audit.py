import unittest

from tools.audit_engine_backfill import audit_records


class EngineBackfillAuditTests(unittest.TestCase):
    def test_proposes_engine_when_existing_record_is_unknown(self):
        summary, candidates, conflicts = audit_records([
            {
                "internal_id": "ITEM-1",
                "title": "[RMXP] Fantasy tileset",
                "engine": ["不明"],
                "url": "https://example.com/tileset",
            }
        ], source_file="fixture.json")
        self.assertEqual(summary["candidate_records"], 1)
        self.assertEqual(candidates[0]["new_specific_engines"], ["XP"])
        self.assertEqual(candidates[0]["old_engine"], ["不明"])
        self.assertEqual(conflicts, [])

    def test_does_not_propose_when_no_concrete_engine_evidence_exists(self):
        summary, candidates, conflicts = audit_records([
            {
                "internal_id": "ITEM-2",
                "title": "Generic icon pack",
                "engine": ["不明"],
                "url": "https://example.com/icons",
            }
        ])
        self.assertEqual(summary.get("candidate_records", 0), 0)
        self.assertEqual(candidates, [])
        self.assertEqual(conflicts, [])

    def test_does_not_propose_engine_already_present(self):
        summary, candidates, conflicts = audit_records([
            {
                "internal_id": "ITEM-3",
                "title": "[RMXP] Tileset",
                "engine": ["XP"],
            }
        ])
        self.assertEqual(summary.get("candidate_records", 0), 0)
        self.assertEqual(candidates, [])
        self.assertEqual(conflicts, [])

    def test_existing_specific_engine_conflict_is_separated(self):
        summary, candidates, conflicts = audit_records([
            {
                "internal_id": "ITEM-CONFLICT",
                "title": "Futuristic Outlands | Weird Structures in a Forest",
                "engine": ["MV"],
                "source_tags": ["rpgmakermz"],
            }
        ])
        self.assertEqual(summary.get("candidate_records", 0), 0)
        self.assertEqual(summary["engine_conflict_records"], 1)
        self.assertEqual(candidates, [])
        self.assertEqual(conflicts[0]["old_engine"], ["MV"])
        self.assertEqual(conflicts[0]["new_specific_engines"], ["MZ"])

    def test_additional_engine_is_candidate_when_old_engine_is_also_detected(self):
        summary, candidates, conflicts = audit_records([
            {
                "internal_id": "ITEM-MULTI",
                "title": "RPG Maker MV/MZ resource pack",
                "engine": ["MV"],
            }
        ])
        self.assertEqual(summary["candidate_records"], 1)
        self.assertEqual(candidates[0]["new_specific_engines"], ["MZ"])
        self.assertEqual(conflicts, [])

    def test_audit_counts_malformed_records_separately(self):
        summary, _, _ = audit_records([
            {"title": "A resource", "engine": ["不明"]},
            None,
            "not a record",
        ])
        self.assertEqual(summary["records"], 1)
        self.assertEqual(summary["invalid_records"], 2)

    def test_preserves_multiple_supported_engines(self):
        _, candidates, conflicts = audit_records([
            {
                "internal_id": "ITEM-4",
                "title": "[XP/VX/VXA] Resource pack",
                "engine": ["不明"],
            }
        ])
        self.assertEqual(
            set(candidates[0]["new_specific_engines"]),
            {"XP", "VX", "VX Ace"},
        )
        self.assertEqual(conflicts, [])


if __name__ == "__main__":
    unittest.main()
