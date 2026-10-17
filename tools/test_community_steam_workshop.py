import unittest
from unittest.mock import patch

from sources.community_steam_workshop import extract_items, normalize_url, get_items


class SteamWorkshopTests(unittest.TestCase):
    def test_normalizes_only_workshop_item_urls(self):
        self.assertEqual(
            normalize_url("https://steamcommunity.com/sharedfiles/filedetails/?id=12345"),
            "https://steamcommunity.com/sharedfiles/filedetails/?id=12345",
        )
        self.assertIsNone(normalize_url("https://example.com/sharedfiles/filedetails/?id=12345"))
        self.assertIsNone(normalize_url("https://steamcommunity.com/sharedfiles/filedetails/?id=abc"))

    def test_extracts_titles_and_deduplicates_urls(self):
        html = """
        <div class="workshopItem">
          <a href="/sharedfiles/filedetails/?id=12345">
            <div class="workshopItemTitle">Battle Plugin</div>
          </a>
        </div>
        <div class="workshopItem">
          <a href="/sharedfiles/filedetails/?id=12345&searchtext=plugin">
            <div class="workshopItemTitle">Battle Plugin</div>
          </a>
        </div>
        """
        items = extract_items(html, "プラグイン")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Battle Plugin")
        self.assertEqual(items[0]["category"], "プラグイン")
        self.assertEqual(items[0]["language"], "多言語")

    @patch("sources.community_steam_workshop.get_html")
    def test_baseline_does_not_emit_existing_workshop_items(self, mock_get_html):
        mock_get_html.return_value = (
            '<a href="/sharedfiles/filedetails/?id=12345">'
            '<div class="workshopItemTitle">Battle Plugin</div></a>'
        )
        items, seen = get_items([])
        self.assertEqual(items, [])
        self.assertEqual(seen, ["https://steamcommunity.com/sharedfiles/filedetails/?id=12345"])
        self.assertEqual(mock_get_html.call_count, 5)

    @patch("sources.community_steam_workshop.get_html")
    def test_emits_new_items_after_baseline(self, mock_get_html):
        mock_get_html.side_effect = [
            '<a href="/sharedfiles/filedetails/?id=12345"><div class="workshopItemTitle">Battle Plugin</div></a>',
            '<a href="/sharedfiles/filedetails/?id=23456"><div class="workshopItemTitle">Tileset Pack</div></a>',
            '<a href="/sharedfiles/filedetails/?id=34567"><div class="workshopItemTitle">Music Pack</div></a>',
            '<a href="/sharedfiles/filedetails/?id=45678"><div class="workshopItemTitle">SFX Pack</div></a>',
            '<a href="/sharedfiles/filedetails/?id=56789"><div class="workshopItemTitle">Resource Pack</div></a>',
        ]
        items, seen = get_items(["already-seen"])
        self.assertEqual(len(items), 5)
        self.assertEqual(len(seen), 6)


if __name__ == "__main__":
    unittest.main()
