import json
import unittest
from pathlib import Path

from asset_metadata import build_asset_metadata
from item_model import normalize_item
from report_formatters import format_deviantart_detail


ROOT = Path(__file__).resolve().parents[1]


class CanonicalItemModelTests(unittest.TestCase):
    def test_tips_becomes_development_info_without_changing_legacy_category(self):
        item = normalize_item(
            {
                "title": "RPG Maker lighting tips",
                "url": "https://example.com/tips",
                "category": "RedditTips",
            },
            "community_reddit",
        )

        self.assertEqual(item["content_type"], "development_info")
        self.assertEqual(item["development_info_type"], "tip")
        self.assertEqual(item["category"], "RedditTips")

    def test_development_info_category_keeps_existing_slack_group(self):
        from report_formatters import get_display_category, get_report_group

        self.assertEqual(get_display_category("開発情報"), "開発情報")
        self.assertEqual(get_report_group("開発情報"), "開発情報・Tips")
        self.assertEqual(get_report_group("RedditTips"), "開発情報・Tips")

    def test_development_tool_is_not_stored_as_asset_type(self):
        item = normalize_item(
            {
                "title": "RPG Maker development helper",
                "url": "https://example.com/tool",
                "category": "開発情報",
                "asset_type": "development_tool",
            },
            "community_reddit",
        )

        self.assertEqual(item["content_type"], "development_info")
        self.assertEqual(item["development_info_type"], "development_tool")
        self.assertIsNone(item["asset_type"])

    def test_runtime_player_stays_outside_asset_taxonomy(self):
        normalized = normalize_item(
            {
                "title": "RPG Maker iOS Player",
                "url": "https://example.com/player",
                "category": "開発情報",
                "development_info_type": "runtime_player",
                "supported_platforms": ["iOS"],
            },
            "community_reddit",
        )
        item = build_asset_metadata(normalized)

        self.assertEqual(item["content_type"], "development_info")
        self.assertEqual(item["development_info_type"], "runtime_player")
        self.assertIsNone(item["asset_type"])
        self.assertEqual(item["supported_platforms"], ["iOS"])
        self.assertTrue(item["engine_relevant"])
        self.assertEqual(item["classification_status"], "not_applicable")
        self.assertEqual(item["subcategory"], [])

    def test_existing_plugin_classification_is_unchanged(self):
        normalized = normalize_item(
            {
                "title": "Battle plugin",
                "url": "https://example.com/plugin",
                "category": "Redditプラグイン",
            },
            "community_reddit",
        )
        item = build_asset_metadata(normalized)

        self.assertEqual(item["content_type"], "plugin")
        self.assertEqual(item["asset_type"], "plugin")

    def test_deviantart_id_and_unix_timestamp_are_normalized(self):
        item = normalize_item(
            {
                "title": "A DeviantArt asset",
                "url": "https://www.deviantart.com/example/art/asset",
                "category": "グラフィック素材",
                "deviationid": "deviation-123",
                "published_time": "1413738356",
                "collector_metadata": {
                    "deviantart": {
                        "is_downloadable": True,
                        "content_width": 400,
                    }
                },
            },
            "official_deviantart",
        )

        self.assertEqual(item["source_item_id"], "deviation-123")
        self.assertEqual(item["source_published_at"], "2014-10-19T17:05:56+00:00")
        self.assertTrue(item["collector_metadata"]["deviantart"]["is_downloadable"])

    def test_links_and_platforms_are_kept_as_separate_structured_fields(self):
        item = normalize_item(
            {
                "title": "Cross-platform tool",
                "url": "https://example.com/original-post",
                "category": "開発情報",
                "development_info_type": "development_tool",
                "supported_platforms": ["Windows", "Linux"],
                "links": [
                    {"type": "download", "url": "https://example.com/download", "status": "available"},
                    {"type": "documentation", "url": "https://example.com/docs"},
                    {"type": "invalid", "url": ""},
                ],
            },
            "community_reddit",
        )

        self.assertEqual(item["url"], "https://example.com/original-post")
        self.assertEqual(item["supported_platforms"], ["Windows", "Linux"])
        self.assertEqual(len(item["links"]), 2)
        self.assertEqual(item["links"][0]["type"], "download")

    def test_deviantart_formatter_reads_namespaced_metadata_and_legacy_fields(self):
        lines = format_deviantart_detail(
            {
                "collector_metadata": {
                    "deviantart": {
                        "is_downloadable": True,
                        "content_width": 400,
                        "content_height": 306,
                    }
                }
            }
        )
        self.assertIn("  ダウンロード：可能", lines)
        self.assertIn("  サイズ：400 × 306", lines)

        legacy_lines = format_deviantart_detail(
            {
                "is_downloadable": False,
                "content_width": 10,
                "content_height": 20,
            }
        )
        self.assertIn("  ダウンロード：不可", legacy_lines)
        self.assertIn("  サイズ：10 × 20", legacy_lines)

    def test_schema_v8_declares_common_and_extension_fields(self):
        schema = json.loads(
            (ROOT / "data" / "schema" / "item_schema.json").read_text(encoding="utf-8")
        )
        fields = schema["fields"]

        self.assertEqual(schema["version"], 8)
        self.assertIn("development_info", fields["content_type"]["enum"])
        for field in (
            "development_info_type",
            "supported_platforms",
            "links",
            "publisher",
            "price_amount",
            "price_currency",
            "release_date",
            "collector_metadata",
            "source_site_name",
            "source_site_type",
            "source_site_language",
            "engine_relevant",
            "file_formats",
            "graphic_style",
            "graphic_theme",
        ):
            self.assertIn(field, fields)


if __name__ == "__main__":
    unittest.main()
