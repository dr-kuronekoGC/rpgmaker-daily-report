import json
import unittest
from unittest.mock import patch

from sources.community_rpgmaker_es import classify, parse_discussions, get_items


class SpanishCommunityTests(unittest.TestCase):
    def test_classifies_plugins_and_assets(self):
        self.assertEqual(
            classify("Nuevo plugin para RPG Maker MZ"),
            "Comunidad RPG Maker ESプラグイン",
        )
        self.assertEqual(
            classify("Tileset de bosque para MV", "Recursos Gráficos"),
            "Comunidad RPG Maker ESグラフィック素材",
        )
        self.assertEqual(
            classify("Música de batalla", "Recursos"),
            "Comunidad RPG Maker ESサウンド素材",
        )

    def test_skips_help_requests(self):
        self.assertIsNone(classify("Ayuda: necesito un plugin"))

    def test_parses_flarum_discussion_and_resource_tag(self):
        payload = {
            "data": [{
                "type": "discussions",
                "id": "42",
                "attributes": {
                    "title": "Nuevo plugin para MZ",
                    "slug": "42-nuevo-plugin-para-mz",
                },
                "relationships": {
                    "tags": {"data": [{"type": "tags", "id": "7"}]}
                },
            }],
            "included": [{
                "type": "tags",
                "id": "7",
                "attributes": {"name": "Complementos"},
            }],
            "links": {"next": None},
        }
        discussions, next_url = parse_discussions(json.dumps(payload))
        self.assertEqual(len(discussions), 1)
        self.assertEqual(discussions[0]["url"], "https://comunidad.rpgmaker.es/d/42-nuevo-plugin-para-mz")
        self.assertEqual(discussions[0]["tags"], "Complementos")
        self.assertIsNone(next_url)

    @patch("sources.community_rpgmaker_es.get_html")
    def test_baseline_records_discussions_without_emitting_old_items(self, mock_get_html):
        mock_get_html.return_value = json.dumps({
            "data": [{
                "type": "discussions",
                "id": "42",
                "attributes": {
                    "title": "Nuevo plugin para MZ",
                    "slug": "42-nuevo-plugin-para-mz",
                },
                "relationships": {"tags": {"data": []}},
            }],
            "included": [],
            "links": {"next": None},
        })
        items, seen = get_items([])
        self.assertEqual(items, [])
        self.assertEqual(seen, ["https://comunidad.rpgmaker.es/d/42-nuevo-plugin-para-mz"])
        mock_get_html.assert_called_once()

    @patch("sources.community_rpgmaker_es.get_html")
    def test_emits_new_resource_discussions(self, mock_get_html):
        mock_get_html.return_value = json.dumps({
            "data": [{
                "type": "discussions",
                "id": "43",
                "attributes": {
                    "title": "Música de batalla",
                    "slug": "43-musica-de-batalla",
                },
                "relationships": {"tags": {"data": []}},
            }],
            "included": [],
            "links": {"next": None},
        })
        items, seen = get_items(["already-seen"])
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["category"], "Comunidad RPG Maker ESサウンド素材")
        self.assertEqual(items[0]["language"], "es")
        self.assertEqual(len(seen), 2)

    @patch("sources.community_rpgmaker_es.get_html")
    def test_keeps_first_page_results_when_second_page_returns_404(self, mock_get_html):
        import requests

        first_page = json.dumps({
            "data": [{
                "type": "discussions",
                "id": "44",
                "attributes": {
                    "title": "Nuevo plugin para MZ",
                    "slug": "44-nuevo-plugin-para-mz",
                },
                "relationships": {"tags": {"data": []}},
            }],
            "included": [],
            "links": {"next": "https://comunidad.rpgmaker.es/api/discussions?page%5Boffset%5D=50"},
        })
        response = requests.Response()
        response.status_code = 404
        second_page_error = requests.HTTPError("404 Client Error", response=response)
        mock_get_html.side_effect = [first_page, second_page_error]

        items, seen = get_items(["already-seen"])

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Nuevo plugin para MZ")
        self.assertIn("https://comunidad.rpgmaker.es/d/44-nuevo-plugin-para-mz", seen)
        self.assertEqual(mock_get_html.call_count, 2)

    @patch("sources.community_rpgmaker_es.get_html", return_value='{"data":[],"links":{"next":null}}')
    def test_empty_api_response_raises_instead_of_being_treated_as_no_new_items(self, mock_get_html):
        with self.assertRaisesRegex(ValueError, "refusing an empty scan"):
            get_items(["already-seen"])
        mock_get_html.assert_called_once()


if __name__ == "__main__":
    unittest.main()
