import tempfile
import unittest
from pathlib import Path
import json

from tools.prepare_engine_backfill_pr import prepare_preview_copies, validate_engine_only_change


class PrepareEngineBackfillPRTests(unittest.TestCase):
    def test_allows_only_engine_field_change(self):
        original = {"meta": {"keep": True}, "items": [
            {"internal_id": "A", "title": "Icon set", "engine": ["不明"], "tags": ["icon"]},
        ]}
        preview = {"meta": {"keep": True}, "items": [
            {"internal_id": "A", "title": "Icon set", "engine": ["MZ"], "tags": ["icon"]},
        ]}
        self.assertEqual(validate_engine_only_change(original, preview), 1)

    def test_rejects_other_field_changes(self):
        original = {"items": [{"title": "Icon set", "engine": ["不明"], "description": "old"}]}
        preview = {"items": [{"title": "Icon set", "engine": ["MZ"], "description": "changed"}]}
        with self.assertRaisesRegex(ValueError, "fields other than engine"):
            validate_engine_only_change(original, preview)

    def test_rejects_record_count_changes(self):
        with self.assertRaisesRegex(ValueError, "record count"):
            validate_engine_only_change({"items": []}, {"items": [{"title": "extra"}]})

    def test_rejects_top_level_metadata_changes(self):
        with self.assertRaisesRegex(ValueError, "non-record metadata"):
            validate_engine_only_change({"meta": 1, "items": []}, {"meta": 2, "items": []})

    def test_copies_only_after_all_monthly_previews_validate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archives = root / "data" / "archive"
            previews = root / "preview"
            archives.mkdir(parents=True)
            previews.mkdir()
            original = {"items": [{"title": "A", "engine": ["不明"]}]}
            valid = {"items": [{"title": "A", "engine": ["MZ"]}]}
            (archives / "2026-09.json").write_text(json.dumps(original), encoding="utf-8")
            (archives / "2026-10.json").write_text(json.dumps(original), encoding="utf-8")
            (previews / "2026-09.json").write_text(json.dumps(valid), encoding="utf-8")
            (previews / "2026-10.json").write_text(json.dumps({"items": [{"title": "B", "engine": ["MZ"]}]}), encoding="utf-8")
            with self.assertRaises(ValueError):
                prepare_preview_copies(archives, previews)
            self.assertEqual(json.loads((archives / "2026-09.json").read_text(encoding="utf-8")), original)


if __name__ == "__main__":
    unittest.main()
