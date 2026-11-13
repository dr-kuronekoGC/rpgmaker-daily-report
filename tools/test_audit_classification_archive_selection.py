import json
import tempfile
import unittest
from pathlib import Path

from audit_classification import load_latest_archive


class LoadLatestArchiveTests(unittest.TestCase):
    def test_ignores_archive_metadata_json_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_dir = Path(tmp)
            (archive_dir / "2026-09.json").write_text(
                json.dumps([{"month": "2026-09"}]), encoding="utf-8"
            )
            (archive_dir / "2026-11.json").write_text(
                json.dumps([{"month": "2026-11"}]), encoding="utf-8"
            )
            (archive_dir / "archive_index.json").write_text(
                json.dumps({"items": []}), encoding="utf-8"
            )
            (archive_dir / "source_status_overrides.json").write_text(
                json.dumps({"source_site_status": "closed", "items": []}),
                encoding="utf-8",
            )

            path, items = load_latest_archive(archive_dir)

            self.assertEqual(path.name, "2026-11.json")
            self.assertEqual(items, [{"month": "2026-11"}])

    def test_returns_empty_when_no_monthly_archive_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_dir = Path(tmp)
            (archive_dir / "source_status_overrides.json").write_text(
                json.dumps({"items": []}), encoding="utf-8"
            )

            path, items = load_latest_archive(archive_dir)

            self.assertIsNone(path)
            self.assertEqual(items, [])


if __name__ == "__main__":
    unittest.main()
