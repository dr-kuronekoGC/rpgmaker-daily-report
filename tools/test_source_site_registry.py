import json
import unittest
from pathlib import Path

from sources.registry import SOURCES


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SITES_FILE = REPOSITORY_ROOT / "data" / "sites" / "sites.json"


class SourceSiteRegistryTests(unittest.TestCase):
    def test_every_active_collector_has_a_registered_site_id(self):
        with SITES_FILE.open("r", encoding="utf-8") as file:
            sites = json.load(file)

        registered_collectors = {
            site["collector"]: site["source_site_id"]
            for site in sites
            if isinstance(site, dict)
            and site.get("collector")
            and site.get("source_site_id")
        }

        missing = sorted(
            source.__name__.split(".")[-1]
            for source in SOURCES
            if source.__name__.split(".")[-1] not in registered_collectors
        )
        self.assertEqual(
            missing,
            [],
            f"Active collectors missing from data/sites/sites.json: {missing}",
        )

    def test_site_ids_are_unique(self):
        with SITES_FILE.open("r", encoding="utf-8") as file:
            sites = json.load(file)

        ids = [
            site["source_site_id"]
            for site in sites
            if isinstance(site, dict) and site.get("source_site_id")
        ]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate source_site_id values")


if __name__ == "__main__":
    unittest.main()
