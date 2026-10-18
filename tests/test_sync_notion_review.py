import unittest

from tools.sync_notion_review import REVIEWED, NOT_REVIEWED, sync_state


def notion_page(pre_id, url, status=NOT_REVIEWED, priority="通常", page_id=None):
    return {
        "id": page_id or f"page-{pre_id}",
        "properties": {
            "PRE番号": {"title": [{"plain_text": pre_id}]},
            "URL": {"url": url},
            "確認優先度": {"select": {"name": priority}},
            "確認状態": {"select": {"name": status}},
        },
    }


class SyncStateTests(unittest.TestCase):
    def setUp(self):
        self.queue = {
            "version": 1,
            "next_pre_number": 4,
            "items": [
                {"pre_id": "PRE-00001", "status": "open", "decision": None, "url": "https://example.com/1"},
                {"pre_id": "PRE-00002", "status": "resolved", "decision": "plugin", "url": "https://example.com/2"},
                {"pre_id": "PRE-00003", "status": "open", "decision": None, "url": "https://example.com/3"},
            ],
        }

    def test_notion_done_resolves_open_item_without_overwriting_existing_decision(self):
        pages = [
            notion_page("PRE-00001", "https://example.com/1", status=REVIEWED),
            notion_page("PRE-00002", "https://example.com/2", status=NOT_REVIEWED),
        ]
        updated, page_updates, creates, summary = sync_state(self.queue, pages, now="2026-10-18T12:00:00+09:00")
        item = next(x for x in updated["items"] if x["pre_id"] == "PRE-00001")
        self.assertEqual(item["status"], "resolved")
        self.assertEqual(item["decision"], "reviewed_in_notion")
        self.assertEqual(item["resolved_at"], "2026-10-18T12:00:00+09:00")
        self.assertEqual(summary["resolved_from_notion"], ["PRE-00001"])
        self.assertEqual(next(x for x in page_updates if x[0] == "page-PRE-00002")[1]["確認状態"]["select"]["name"], REVIEWED)
        self.assertEqual(creates[0]["properties"]["PRE番号"]["title"][0]["text"]["content"], "PRE-00003")

    def test_existing_resolved_decision_is_not_overwritten(self):
        pages = [notion_page("PRE-00002", "https://example.com/2", status=NOT_REVIEWED)]
        updated, page_updates, _, _ = sync_state(self.queue, pages)
        item = next(x for x in updated["items"] if x["pre_id"] == "PRE-00002")
        self.assertEqual(item["decision"], "plugin")
        self.assertEqual(item["status"], "resolved")
        self.assertEqual(page_updates[0][1]["確認状態"]["select"]["name"], REVIEWED)

    def test_url_is_refreshed_without_resetting_priority_or_status(self):
        pages = [
            notion_page("PRE-00001", "https://old.example/1", priority="高"),
            notion_page("PRE-00002", "https://example.com/2", status=REVIEWED),
        ]
        _, page_updates, _, _ = sync_state(self.queue, pages)
        update = next(x[1] for x in page_updates if x[0] == "page-PRE-00001")
        self.assertEqual(update["URL"]["url"], "https://example.com/1")
        self.assertNotIn("確認優先度", update)
        self.assertNotIn("確認状態", update)

    def test_duplicate_notion_pre_ids_fail_closed(self):
        pages = [
            notion_page("PRE-00001", "https://example.com/1"),
            notion_page("PRE-00001", "https://example.com/duplicate", page_id="duplicate"),
        ]
        with self.assertRaisesRegex(ValueError, "Duplicate PRE ID in Notion"):
            sync_state(self.queue, pages)


if __name__ == "__main__":
    unittest.main()
