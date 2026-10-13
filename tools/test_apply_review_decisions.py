import unittest

from tools.apply_review_decisions import apply_decisions, validate_decisions


def make_queue():
    return {
        "version": 1,
        "items": [
            {
                "pre_id": "PRE-00001", "status": "open",
                "decision": None, "resolved_at": None, "review_note": None,
            },
            {
                "pre_id": "PRE-00002", "status": "resolved",
                "decision": "confirmed", "resolved_at": "2026-10-01T12:00:00+09:00",
                "review_note": "resource",
            },
        ],
    }


class ReviewDecisionImportTests(unittest.TestCase):
    def test_dry_run_returns_updated_copy_without_mutating_original(self):
        queue = make_queue()
        payload = {"decisions": [{"pre_id": "PRE-00001", "decision": "plugin", "note": "Reusable plugin"}]}
        updated, summary = apply_decisions(queue, payload, resolved_at="2026-10-13T12:00:00+09:00")

        self.assertEqual(queue["items"][0]["status"], "open")
        self.assertEqual(updated["items"][0]["status"], "resolved")
        self.assertEqual(updated["items"][0]["decision"], "plugin")
        self.assertEqual(updated["items"][0]["review_note"], "Reusable plugin")
        self.assertEqual(updated["items"][0]["resolved_at"], "2026-10-13T12:00:00+09:00")
        self.assertEqual(summary["applied"], 1)

    def test_validation_failure_does_not_return_partial_changes(self):
        queue = make_queue()
        payload = {"decisions": [
            {"pre_id": "PRE-00001", "decision": "plugin"},
            {"pre_id": "PRE-99999", "decision": "exclude"},
        ]}
        with self.assertRaisesRegex(ValueError, "does not exist"):
            apply_decisions(queue, payload)
        self.assertEqual(queue["items"][0]["status"], "open")

    def test_conflicting_decision_for_resolved_item_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "already resolved"):
            validate_decisions(
                {"decisions": [{"pre_id": "PRE-00002", "decision": "not_applicable", "note": "different"}]},
                make_queue(),
            )

    def test_identical_already_applied_decision_is_idempotent(self):
        queue = make_queue()
        payload = {"decisions": [{"pre_id": "PRE-00002", "decision": "confirmed", "note": "resource"}]}
        updated, summary = apply_decisions(queue, payload)
        self.assertEqual(summary["applied"], 0)
        self.assertEqual(summary["already_applied"], 1)
        self.assertEqual(updated, queue)

    def test_duplicate_decision_ids_are_rejected(self):
        payload = {"decisions": [
            {"pre_id": "PRE-00001", "decision": "plugin"},
            {"pre_id": "PRE-00001", "decision": "material"},
        ]}
        with self.assertRaisesRegex(ValueError, "Duplicate decision"):
            validate_decisions(payload, make_queue())

    def test_empty_decision_batch_is_valid_noop(self):
        updated, summary = apply_decisions(make_queue(), {"decisions": []})
        self.assertEqual(summary["applied"], 0)
        self.assertEqual(summary["requested"], 0)


if __name__ == "__main__":
    unittest.main()
