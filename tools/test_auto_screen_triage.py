import unittest
from unittest.mock import Mock

from fetch_historical_review_bodies import parse_html

from auto_screen_open_reviews import (
    all_delivery_links_dead,
    classify_page,
    confirmed_resource_decision,
    is_delivery_link,
    resource_kind,
)


def link(url, *, reachable=False, dead=False, error=None, text=""):
    return {
        "url": url,
        "text": text,
        "reachable": reachable,
        "dead": dead,
        "error": error,
        "http_status": 200 if reachable else (404 if dead else None),
    }


class ForumBodyExtractionTests(unittest.TestCase):
    def test_first_post_sets_intent_but_all_thread_assets_are_checked(self):
        html = """
        <html><head><title>Post your Battlers here</title>
        <meta name="description" content="Short excerpt only."></head>
        <body><div id="content">
          <div class="postarea">
            <div class="postbody">
              This is the original resource post. Community members can share battler images
              they created themselves, and should credit the artist. The thread collects
              reusable assets for the community.
            </div>
            <a href="https://example.com/first.zip">First-post download</a>
          </div>
          <div class="postarea">
            <div class="postbody">
              A later reply talks about a pirate character and mentions something ripped from
              another game. Those words must not change the original post's classification.
            </div>
            <a href="https://example.com/reply.zip">Reply attachment</a>
            <img src="/media/attachments/CharSet.png" alt="CharSet preview">
          </div>
        </div></body></html>
        """
        response = Mock()
        response.status_code = 200
        response.url = "https://example.com/topic"
        response.text = html
        response.raise_for_status = Mock()
        session = Mock()
        session.get.return_value = response

        page = parse_html(session, "https://example.com/topic")

        self.assertIn("original resource post", page["body_text"])
        self.assertNotIn("ripped from", page["body_text"])
        urls = {link["url"] for link in page["outbound_links"]}
        self.assertIn("https://example.com/first.zip", urls)
        self.assertIn("https://example.com/reply.zip", urls)
        self.assertIn("https://example.com/media/attachments/CharSet.png", urls)
        image = next(link for link in page["outbound_links"] if link["url"].endswith("CharSet.png"))
        self.assertEqual(image["link_kind"], "embedded_image")



class ResourceEvidenceTests(unittest.TestCase):
    def test_live_music_download_is_confirmable(self):
        checks = {
            "results": [
                link("https://drive.google.com/open?id=sample", reachable=True)
            ]
        }
        result = confirmed_resource_decision(
            "Музыка и не очень", "Tracks are available here.", checks
        )
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "confirmed")

    def test_title_type_overrides_unrelated_terms_in_long_body(self):
        self.assertEqual(
            resource_kind("[MZ] CharSet 2003 в MZ (оригинальный размер)", "music, audio, and soundtracks"),
            "graphics",
        )
        self.assertIsNone(
            resource_kind("Озвучка текста", "A forum discussion about a text-to-speech bot, with unrelated footer links."),
        )

    def test_pirate_theme_is_not_mistaken_for_piracy(self):
        item = {
            "pre_id": "PRE-00373",
            "url": "https://rmrk.net/index.php?topic=28572.0",
            "title": "Post your Battlers here.",
        }
        page = {
            "page_title": "Post your Battlers here.",
            "body_text": "Community members can share battler images. Pirates: a pirate captain and a female thief.",
            "http_status": 200,
            "retrieval_status": "body_found",
            "resource_link_check": {"results": []},
        }
        result = classify_page(item, page)
        self.assertFalse(result and result[0] == "exclude")

    def test_explicit_pirate_archive_tag_is_still_excluded(self):
        item = {
            "pre_id": "PRE-00386",
            "url": "https://example.com/archive",
            "title": "[PIRATE] RMWEB - Общие ресурсы",
        }
        page = {
            "page_title": "[PIRATE] RMWEB - Общие ресурсы",
            "body_text": "An explicitly pirated archive.",
            "http_status": 200,
            "retrieval_status": "body_found",
            "resource_link_check": {"results": []},
        }
        result = classify_page(item, page)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "exclude")

    def test_dead_music_download_not_rescued_by_live_cover_art(self):
        checks = {
            "all_checked_dead": False,
            "results": [
                link(
                    "https://rpgmaker.ru/media/kunena/attachments/19137/cover.png",
                    reachable=True,
                ),
                link("https://drive.google.com/open?id=dead1", dead=True),
                link("https://drive.google.com/open?id=dead2", dead=True),
            ],
        }
        self.assertTrue(
            all_delivery_links_dead("Альбом: Out of control", "Треки", checks)
        )

    def test_live_or_inconclusive_download_prevents_dead_link_exclusion(self):
        checks = {
            "results": [
                link("https://drive.google.com/open?id=dead", dead=True),
                link("https://drive.google.com/open?id=live", reachable=True),
                link("https://drive.google.com/open?id=unknown", error="ReadTimeout"),
            ]
        }
        self.assertFalse(
            all_delivery_links_dead("Коллекция Саундтреков", "Музыка", checks)
        )

    def test_human_reopen_note_overrides_dead_link_rules(self):
        item = {
            "pre_id": "PRE-00507",
            "url": "https://example.com/topic",
            "review_note": "自動判定を取り消し。未確認に戻す。",
        }
        page = {
            "page_title": "Стрепня от MaraMonstr'а",
            "body_text": "A post with resource links.",
            "http_status": 200,
            "retrieval_status": "body_found",
            "resource_link_check": {
                "all_checked_dead": True,
                "results": [link("https://yadi.sk/d/dead", dead=True)],
            },
        }
        self.assertIsNone(classify_page(item, page))

    def test_request_post_is_not_auto_confirmed_even_with_live_link(self):
        checks = {
            "results": [
                link("https://drive.google.com/open?id=sample", reachable=True)
            ]
        }
        result = confirmed_resource_decision(
            "Looking for sprites", "Can someone share sprites?", checks
        )
        self.assertIsNone(result)

    def test_semantic_attachment_can_be_asset_but_random_preview_cannot(self):
        self.assertTrue(
            is_delivery_link(
                link(
                    "https://rpgmaker.ru/media/kunena/attachments/1/CharSet2003MZ.png",
                    reachable=True,
                ),
                "graphics",
            )
        )
        self.assertFalse(
            is_delivery_link(
                link(
                    "https://rpgmaker.ru/media/kunena/attachments/1/0bbb4b2952bcbe12.jpg",
                    reachable=True,
                ),
                "graphics",
            )
        )
        self.assertTrue(
            is_delivery_link(
                link(
                    "https://rpgmaker.ru/media/kunena/attachments/1/butterfly.png",
                    reachable=True,
                ),
                "graphics",
            )
        )


if __name__ == "__main__":
    unittest.main()
