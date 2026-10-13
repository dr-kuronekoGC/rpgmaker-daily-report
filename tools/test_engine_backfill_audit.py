import unittest
from tools.audit_engine_backfill import audit_records


class EngineBackfillAuditTests(unittest.TestCase):
    def test_unknown_engine_with_specific_evidence_is_candidate(self):
        summary, candidates, conflicts = audit_records([{
            "internal_id": "ITEM-1", "title": "[RMXP] Fantasy tileset",
            "engine": ["不明"], "url": "https://example.com/tileset",
        }], source_file="fixture.json")
        self.assertEqual(summary["candidate_records"], 1)
        self.assertEqual(candidates[0]["new_specific_engines"], ["XP"])
        self.assertEqual(candidates[0]["old_engine"], ["不明"])
        self.assertEqual(conflicts, [])

    def test_no_concrete_evidence_is_not_a_candidate(self):
        summary, candidates, conflicts = audit_records([{
            "internal_id": "ITEM-2", "title": "Generic icon pack",
            "engine": ["不明"], "url": "https://example.com/icons",
        }])
        self.assertEqual(summary.get("candidate_records", 0), 0)
        self.assertEqual(candidates, [])
        self.assertEqual(conflicts, [])

    def test_engine_already_present_is_not_a_candidate(self):
        summary, candidates, conflicts = audit_records([{
            "internal_id": "ITEM-3", "title": "[RMXP] Tileset", "engine": ["XP"],
        }])
        self.assertEqual(summary.get("candidate_records", 0), 0)
        self.assertEqual(candidates, [])
        self.assertEqual(conflicts, [])

    def test_disjoint_existing_engine_is_reported_as_conflict(self):
        summary, candidates, conflicts = audit_records([{
            "internal_id": "ITEM-CONFLICT",
            "title": "Futuristic Outlands | Weird Structures in a Forest",
            "engine": ["MV"], "source_tags": ["rpgmakermz"],
        }])
        self.assertEqual(summary.get("candidate_records", 0), 0)
        self.assertEqual(summary["engine_conflict_records"], 1)
        self.assertEqual(candidates, [])
        self.assertEqual(conflicts[0]["old_engine"], ["MV"])
        self.assertEqual(conflicts[0]["new_specific_engines"], ["MZ"])

    def test_explicit_multi_engine_signal_is_a_candidate(self):
        summary, candidates, conflicts = audit_records([{
            "internal_id": "ITEM-MULTI",
            "title": "[RMMV/RMMZ] resource pack", "engine": ["MV"],
        }])
        self.assertEqual(summary["candidate_records"], 1)
        self.assertEqual(candidates[0]["new_specific_engines"], ["MZ"])
        self.assertEqual(conflicts, [])

    def test_malformed_records_are_counted(self):
        summary, _, _ = audit_records([
            {"title": "A resource", "engine": ["不明"]}, None, "not a record",
        ])
        self.assertEqual(summary["records"], 1)
        self.assertEqual(summary["invalid_records"], 2)

    def test_multiple_supported_engines_are_preserved(self):
        _, candidates, conflicts = audit_records([{
            "internal_id": "ITEM-4", "title": "[XP/VX/VXA] Resource pack",
            "engine": ["不明"],
        }])
        self.assertEqual(set(candidates[0]["new_specific_engines"]), {"XP", "VX", "VX Ace"})
        self.assertEqual(conflicts, [])


if __name__ == "__main__":
    unittest.main()
