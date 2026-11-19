import unittest

from report import build_report


class ResourceCandidateReportTests(unittest.TestCase):
    def test_resource_candidate_with_needs_review_is_visible_in_slack_report(self):
        report = build_report(
            [
                {
                    "title": "MZero3D Resource",
                    "url": "https://example.com/mzero3d",
                    "source": "RPG Maker Guild",
                    "category": "プラグイン",
                    "resource_intent": "resource_candidate",
                    "classification_status": "needs_review",
                }
            ],
            review_items=[],
            carryover_items=[],
            source_results=[],
        )

        self.assertIn("【📥 素材候補（分類確認中）】", report)
        self.assertIn(
            "<https://example.com/mzero3d|MZero3D Resource>",
            report,
        )
        self.assertIn("[RPG Maker Guild]", report)
        self.assertIn("詳細分類は未確定", report)

    def test_non_candidate_needs_review_item_remains_suppressed(self):
        report = build_report(
            [
                {
                    "title": "Uncertain discussion",
                    "url": "https://example.com/discussion",
                    "source": "Test Forum",
                    "category": "質問",
                    "resource_intent": "discussion",
                    "classification_status": "needs_review",
                }
            ],
            review_items=[],
            carryover_items=[],
            source_results=[],
        )

        self.assertNotIn("Uncertain discussion", report)
        self.assertNotIn("素材候補（分類確認中）", report)


if __name__ == "__main__":
    unittest.main()
