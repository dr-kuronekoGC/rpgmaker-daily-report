import json
import unittest
from pathlib import Path

from sources.registry import SOURCES


ROOT = Path(__file__).resolve().parents[1]


class SourceRegistryConsistencyTests(unittest.TestCase):
    def test_every_site_marked_for_collection_has_a_registered_collector(self):
        sites = json.loads((ROOT / "data" / "sites" / "sites.json").read_text(encoding="utf-8"))
        registered = {source.__name__.split(".")[-1] for source in SOURCES}
        missing = [
            f"{site.get('source_site_id')} {site.get('source_site_name')}: {site.get('collector')}"
            for site in sites
            if site.get("collection") is True and site.get("collector") not in registered
        ]
        self.assertEqual(missing, [])

    def test_retired_rmrk_is_not_scheduled_for_new_collection(self):
        sites = json.loads((ROOT / "data" / "sites" / "sites.json").read_text(encoding="utf-8"))
        rmrk = next(site for site in sites if site.get("source_site_id") == "SITE-00034")
        registered = {source.__name__.split(".")[-1] for source in SOURCES}
        self.assertFalse(rmrk["collection"])
        self.assertNotIn(rmrk["collector"], registered)


if __name__ == "__main__":
    unittest.main()
