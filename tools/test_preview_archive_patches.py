import copy
import unittest

from tools.preview_archive_patches import preview_patches


PRE_ID = "PRE-00543"
INTERNAL_ID = "ITEM-c7309e3d117c4861"
URL = "https://example.com/original-post"


def make_inputs():
    archive_item = {
        "pre_id": PRE_ID,
        "internal_id": INTERNAL_ID,
        "url": URL,
        "content_type": "asset",
        "asset_type": "other",
        "tags": [],
    }
    ledger_item = {
        "pre_id": PRE_ID,
        "internal_id": INTERNAL_ID,
        "url": URL,
        "status": "resolved",
        "decision": "confirmed",
    }
    manifest = {
        "schema_version": 1,
        "target_schema_version": 8,
        "patches": [{
            "pre_id": PRE_ID,
            "internal_id": INTERNAL_ID,
            "source_url": URL,
            "expected": {
                "content_type": "asset",
                "asset_type": "other",
                "development_info_type": None,
                "tags": [],
            },
            "set": {
                "content_type": "development_info",
                "asset_type": None,
                "development_info_type": "runtime_player",
                "tags": ["iPhone", "ゲームプレイヤー"],
            },
            "evidence": {
                "kind": "user_confirmation",
                "note": "User confirmed this is an iPhone player app.",
            },
        }],
    }
    return (
        manifest,
        [archive_item],
        {"items": [ledger_item]},
        {"decisions": [{"pre_id": PRE_ID, "decision": "confirmed", "note": "confirmed"}]},
    )


class ArchivePatchPreviewTests(unittest.TestCase):
    def test_pre_00543_produces_explicit_diff_without_mutating_inputs(self):
        inputs = make_inputs()
        original = copy.deepcopy(inputs)

        result = preview_patches(*inputs)

        self.assertEqual(result[0]["status"], "ready_for_review")
        self.assertEqual(
            {change["field"]: change["after"] for change in result[0]["changes"]},
            {
                "content_type": "development_info",
                "asset_type": None,
                "development_info_type": "runtime_player",
                "tags": ["iPhone", "ゲームプレイヤー"],
            },
        )
        self.assertEqual(inputs, original)

    def test_exact_identity_requires_both_pre_id_and_internal_id(self):
        manifest, archive, ledger, decisions = make_inputs()
        manifest["patches"][0]["internal_id"] = "ITEM-wrong"
        with self.assertRaisesRegex(ValueError, "internal_id does not match"):
            preview_patches(manifest, archive, ledger, decisions)

    def test_archive_duplicate_pre_id_blocks_preview(self):
        manifest, archive, ledger, decisions = make_inputs()
        archive.append(dict(archive[0], title="duplicate"))
        with self.assertRaisesRegex(ValueError, "exactly one match for pre_id"):
            preview_patches(manifest, archive, ledger, decisions)

    def test_archive_duplicate_internal_id_blocks_preview(self):
        manifest, archive, ledger, decisions = make_inputs()
        archive.append({
            "pre_id": "PRE-00999",
            "internal_id": INTERNAL_ID,
            "url": "https://example.com/other",
        })
        with self.assertRaisesRegex(ValueError, "exactly one match for internal_id"):
            preview_patches(manifest, archive, ledger, decisions)

    def test_expected_value_conflict_blocks_preview(self):
        manifest, archive, ledger, decisions = make_inputs()
        archive[0]["asset_type"] = "plugin"
        with self.assertRaisesRegex(ValueError, "expected-value conflict"):
            preview_patches(manifest, archive, ledger, decisions)

    def test_source_url_mismatch_blocks_preview(self):
        manifest, archive, ledger, decisions = make_inputs()
        archive[0]["url"] = "https://example.com/changed"
        with self.assertRaisesRegex(ValueError, "source_url does not match the Archive"):
            preview_patches(manifest, archive, ledger, decisions)

    def test_non_confirmed_ledger_entry_blocks_preview(self):
        manifest, archive, ledger, decisions = make_inputs()
        ledger["items"][0]["decision"] = "not_applicable"
        with self.assertRaisesRegex(ValueError, "not resolved/confirmed"):
            preview_patches(manifest, archive, ledger, decisions)

    def test_non_confirmed_decision_record_blocks_preview(self):
        manifest, archive, ledger, decisions = make_inputs()
        decisions["decisions"][0]["decision"] = "plugin"
        with self.assertRaisesRegex(ValueError, "does not confirm"):
            preview_patches(manifest, archive, ledger, decisions)

    def test_unknown_field_is_rejected(self):
        manifest, archive, ledger, decisions = make_inputs()
        manifest["patches"][0]["set"]["url"] = "https://example.com/new"
        manifest["patches"][0]["expected"]["url"] = URL
        with self.assertRaisesRegex(ValueError, "unsupported fields"):
            preview_patches(manifest, archive, ledger, decisions)

    def test_duplicate_proposals_are_rejected(self):
        manifest, archive, ledger, decisions = make_inputs()
        manifest["patches"].append(copy.deepcopy(manifest["patches"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate patch"):
            preview_patches(manifest, archive, ledger, decisions)

    def test_already_matching_target_is_reported_without_writes(self):
        manifest, archive, ledger, decisions = make_inputs()
        archive[0].update(manifest["patches"][0]["set"])
        result = preview_patches(manifest, archive, ledger, decisions)
        self.assertEqual(result[0]["status"], "already_matches")
        self.assertEqual(result[0]["changes"], [])

    def test_only_explicitly_listed_fields_appear_in_diff(self):
        manifest, archive, ledger, decisions = make_inputs()
        archive[0]["engine"] = ["その他RPG Maker"]
        result = preview_patches(manifest, archive, ledger, decisions)
        changed_fields = {change["field"] for change in result[0]["changes"]}
        self.assertEqual(
            changed_fields,
            {"content_type", "asset_type", "development_info_type", "tags"},
        )
        self.assertEqual(archive[0]["engine"], ["その他RPG Maker"])


if __name__ == "__main__":
    unittest.main()
