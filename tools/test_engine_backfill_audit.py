import unittest

from tools.audit_engine_backfill import audit_records


class EngineBackfillAuditTests(unittest.TestCase):
    def test_proposes_engine_when_existing_record_is_unknown(self):
        summary, candidates = audit_records([
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

    def test_does_not_propose_when_no_concrete_engine_evidence_exists(self):
        summary, candidates = audit_records([
            {
                "internal_id": "ITEM-2",
                "title": "Generic icon pack",
                "engine": ["不明"],
                "url": "https://example.com/icons",
            }
        ])
        self.assertEqual(summary.get("candidate_records", 0), 0)
        self.assertEqual(candidates, [])

    def test_does_not_propose_engine_already_present(self):
        summary, candidates = audit_records([
            {
                "internal_id": "ITEM-3",
                "title": "[RMXP] Tileset",
                "engine": ["XP"],
            }
        ])
        self.assertEqual(summary.get("candidate_records", 0), 0)
        self.assertEqual(candidates, [])

    def test_audit_counts_malformed_records_separately(self):
        summary, _ = audit_records([
            {"title": "A resource", "engine": ["不明"]},
            None,
            "not a record",
        ])
        self.assertEqual(summary["records"], 1)
        self.assertEqual(summary["invalid_records"], 2)

    def test_preserves_multiple_supported_engines(self):
        _, candidates = audit_records([
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


if __name__ == "__main__":
    unittest.main()
