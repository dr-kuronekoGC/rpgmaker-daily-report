import unittest

from tools.audit_open_review_queue import audit_item


class OpenReviewQueueAuditTests(unittest.TestCase):
    def test_explicit_request_is_flagged_as_exclusion_candidate(self):
        item = {
            "pre_id": "PRE-TEST1",
            "internal_id": "ITEM-TEST1",
            "source": "RMRK",
            "title": "Need Char Sets and Battlers",
            "url": "https://example.com/topic",
            "category": "RMRKグラフィック素材",
            "description": "",
            "status": "open",
        }
        result = audit_item(item)
        self.assertEqual(result["suggestion"], "candidate_exclude")
        self.assertEqual(result["audit_intent"], "not_resource")
        self.assertEqual(item["status"], "open")

    def test_insufficient_evidence_stays_in_manual_review(self):
        item = {
            "pre_id": "PRE-TEST2",
            "internal_id": "ITEM-TEST2",
            "source": "Unknown",
            "title": "Interesting post",
            "url": "https://example.com/topic",
            "description": "",
            "status": "open",
        }
        result = audit_item(item)
        self.assertEqual(result["suggestion"], "keep_manual_review")
        self.assertEqual(result["audit_intent"], "uncertain")
        self.assertIn("not an approved human decision", result["warning"])

    def test_asset_keywords_without_distribution_need_body_review(self):
        item = {
            "pre_id": "PRE-TEST3",
            "internal_id": "ITEM-TEST3",
            "source": "RMRK",
            "title": "Post-Apocalyptic Tilesets [RMXP]",
            "url": "https://example.com/topic",
            "category": "RMRKグラフィック素材",
            "description": "",
            "status": "open",
        }
        result = audit_item(item)
        self.assertEqual(result["suggestion"], "needs_body_review")
        self.assertEqual(result["audit_intent"], "resource_candidate")


if __name__ == "__main__":
    unittest.main()
