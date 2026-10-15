import unittest
from unittest.mock import patch

import asset_metadata


class AssetMetadataClassificationReuseTests(unittest.TestCase):
    def test_plugin_taxonomy_is_scored_once_and_reused(self):
        classification = {
            "categories": ["battle"],
            "classification_confidence": "high",
            "classification_status": "auto",
            "classification_margin": 4,
            "classification_scores": {"battle": 4},
            "classification_evidence": [{"signal": "test"}],
        }

        with patch(
            "asset_metadata.classify_taxonomy_with_evidence",
            return_value=classification,
        ) as classify_taxonomy:
            result = asset_metadata.build_asset_metadata(
                {
                    "title": "Battle Plugin",
                    "url": "https://example.com/battle-plugin",
                    "category": "プラグイン",
                    "source_tags": ["RPG Maker MV"],
                }
            )

        self.assertEqual(classify_taxonomy.call_count, 1)
        self.assertEqual(result["subcategory"], ["battle"])
        self.assertEqual(result["plugin_category"], ["battle"])
        self.assertIsNot(result["subcategory"], result["plugin_category"])


if __name__ == "__main__":
    unittest.main()
