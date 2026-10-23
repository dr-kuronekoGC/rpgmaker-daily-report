import unittest
from unittest.mock import Mock

from fetch_historical_review_bodies import body_retrieval_status, parse_html

from auto_screen_open_reviews import (
    all_delivery_links_dead,
    classify_page,
    confirmed_resource_decision,
    check_resource_links,
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
    def test_plain_text_urls_are_collected_and_deduplicated_with_anchors(self):
        html = """
        <html><head><title>Character resources</title></head>
        <body><div class="postbody">
          Download: https://example.com/assets/charset.png.
          <a href="https://example.com/assets/plugin.js">https://example.com/assets/plugin.js</a>
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
        urls = [item["url"] for item in page["outbound_links"]]
        self.assertEqual(urls.count("https://example.com/assets/charset.png"), 1)
        self.assertEqual(urls.count("https://example.com/assets/plugin.js"), 1)
        charset = next(item for item in page["outbound_links"] if item["url"].endswith("charset.png"))
        self.assertEqual(charset["link_kind"], "plain_text_url")
        plugin = next(item for item in page["outbound_links"] if item["url"].endswith("plugin.js"))
        self.assertEqual(plugin["link_kind"], "anchor")

    def test_short_generic_layout_fallback_is_not_verified_post_body(self):
        page = {
            "http_status": 200,
            "retrieval_method": "html",
            "body_text": "Login notice Topic title author and forum navigation",
            "page_description": "",
            "html_diagnostics": {
                "body_source": "#ipsLayout_mainArea",
                "body_selector_used": "#ipsLayout_mainArea",
                "body_text_chars": 52,
            },
        }
        self.assertEqual(body_retrieval_status(page), "body_unverified")

    def test_unverified_body_is_never_auto_resolved(self):
        item = {
            "pre_id": "PRE-TEST-BODY-UNVERIFIED",
            "url": "https://example.com/topic",
            "title": "Icone MZ - stile",
            "review_note": "",
        }
        page = {
            "page_title": item["title"],
            "body_text": "Login notice Topic title author and forum navigation",
            "http_status": 200,
            "retrieval_status": "body_unverified",
            "resource_link_check": {"candidate_count": 0, "results": []},
        }
        self.assertIsNone(classify_page(item, page))

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
    def test_resource_link_audit_preserves_embedded_image_kind(self):
        response = Mock()
        response.status_code = 404
        response.close = Mock()
        session = Mock()
        session.head.return_value = response
        page = {
            "outbound_links": [
                {
                    "text": "embedded image/attachment",
                    "url": "https://img369.imageshack.us/img369/4427/captainpirate1do4.png",
                    "link_kind": "image_anchor",
                }
            ]
        }
        result = check_resource_links(session, page, "https://example.com/topic")
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["results"][0]["link_kind"], "image_anchor")

    def test_external_sprite_images_are_material_links_but_theme_icons_are_not(self):
        external = {
            "url": "http://img369.imageshack.us/img369/4427/captainpirate1do4.png",
            "text": "embedded image/attachment",
            "link_kind": "image_anchor",
            "http_status": 404,
            "dead": True,
            "reachable": False,
            "error": None,
        }
        theme_icon = {
            "url": "https://rmrk.net/Themes/PurpleHaze/images/post/xx.png",
            "text": "embedded image/attachment",
            "link_kind": "embedded_image",
            "http_status": 200,
            "dead": False,
            "reachable": True,
            "error": None,
        }
        self.assertTrue(is_delivery_link(external, "graphics"))
        self.assertFalse(is_delivery_link(theme_icon, "graphics"))
        self.assertFalse(is_delivery_link(external, "audio"))
        self.assertTrue(
            all_delivery_links_dead(
                "Post your Battlers here.",
                "Community battler collection",
                {"results": [external, theme_icon]},
            )
        )

    def test_personal_art_showcase_without_material_links_can_be_excluded(self):
        item = {
            "pre_id": "PRE-00343",
            "url": "https://example.com/topic",
            "title": "battlers i've drawn",
            "review_note": "",
        }
        page = {
            "page_title": "battlers i've drawn",
            "body_text": "I drew these battlers as a personal art showcase; they are free to use, but no asset or download link is present.",
            "http_status": 200,
            "retrieval_status": "body_found",
            "resource_link_check": {"candidate_count": 0, "results": []},
        }
        result = classify_page(item, page)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "not_applicable")

    def test_live_external_sprite_image_can_confirm_a_resource(self):
        checks = {
            "results": [
                {
                    "url": "https://i.imgur.com/sitting-sprite.png",
                    "text": "Sitting sprite",
                    "link_kind": "image_anchor",
                    "http_status": 200,
                    "dead": False,
                    "reachable": True,
                    "error": None,
                }
            ]
        }
        result = confirmed_resource_decision(
            "Sitting sprites RMXP", "Reusable sitting character sprites.", checks
        )
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "confirmed")

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

    def test_solved_resource_request_without_delivery_link_is_excluded(self):
        item = {
            "pre_id": "PRE-TEST-SOLVED-REQUEST",
            "url": "https://example.com/topic",
            "title": "Looking for actors sprites? [SOLVED]",
            "review_note": "",
        }
        page = {
            "page_title": item["title"],
            "body_text": "I was looking for actors sprites, but the question is now solved.",
            "http_status": 200,
            "retrieval_status": "body_found",
            "resource_link_check": {
                "candidate_count": 0,
                "results": [],
            },
        }
        result = classify_page(item, page)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "not_applicable")

    def test_solved_recolor_request_without_delivery_link_is_excluded(self):
        item = {
            "pre_id": "PRE-00367",
            "url": "https://rmrk.net/index.php?topic=30995.0",
            "title": "[Resolved] Battler Hair Recolor",
            "review_note": "",
        }
        page = {
            "page_title": item["title"],
            "body_text": (
                "You may recognize this character. I would very much appreciate it "
                "if someone could recolor this character's hair to be brown. Thanks."
            ),
            "http_status": 200,
            "retrieval_status": "body_found",
            "resource_link_check": {
                "candidate_count": 1,
                "results": [
                    link("https://rmrk.net/Smileys/default/shocked.gif", dead=True, text=":o")
                ],
            },
        }
        result = classify_page(item, page)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "not_applicable")

    def test_withdrawn_resource_request_without_delivery_link_is_excluded(self):
        item = {
            "pre_id": "PRE-00370",
            "url": "https://rmrk.net/index.php?topic=30998.0",
            "title": "[Resolved] Computer Charset for VX",
            "review_note": "",
        }
        page = {
            "page_title": item["title"],
            "body_text": "Request withdrawn.",
            "http_status": 200,
            "retrieval_status": "body_found",
            "resource_link_check": {"candidate_count": 0, "results": []},
        }
        result = classify_page(item, page)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "not_applicable")

    def test_solved_rtp_upload_request_without_delivery_link_is_excluded(self):
        item = {
            "pre_id": "PRE-00226",
            "url": "https://rmrk.net/index.php?topic=32111.0",
            "title": "[Resolved] VX RTP Earth Animation Sheets",
            "review_note": "",
        }
        page = {
            "page_title": item["title"],
            "body_text": (
                "Please up the RTP Earth Animation sheets for VX pls, thx. "
                "I don't have access to a computer with VX on it atm."
            ),
            "http_status": 200,
            "retrieval_status": "body_found",
            "resource_link_check": {
                "candidate_count": 1,
                "results": [
                    link("https://rmrk.net/Smileys/default/sad.gif", dead=True, text=":(")
                ],
            },
        }
        result = classify_page(item, page)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "not_applicable")

    def test_request_to_bump_thread_is_not_mistaken_for_upload_request(self):
        item = {
            "pre_id": "PRE-TEST-BUMP-REQUEST",
            "url": "https://example.com/topic",
            "title": "[Resolved] VX RTP Earth Animation Sheets",
            "review_note": "",
        }
        page = {
            "page_title": item["title"],
            "body_text": "Please up the thread if anyone has more information.",
            "http_status": 200,
            "retrieval_status": "body_found",
            "resource_link_check": {"candidate_count": 0, "results": []},
        }
        self.assertIsNone(classify_page(item, page))

    def test_solved_resource_request_with_inconclusive_delivery_link_stays_open(self):
        item = {
            "pre_id": "PRE-TEST-SOLVED-REQUEST-LINK",
            "url": "https://example.com/topic",
            "title": "Looking for actors sprites? [SOLVED]",
            "review_note": "",
        }
        page = {
            "page_title": item["title"],
            "body_text": "I was looking for actors sprites, but the question is now solved.",
            "http_status": 200,
            "retrieval_status": "body_found",
            "resource_link_check": {
                "candidate_count": 1,
                "results": [
                    link("https://files.example.com/sprites.zip", error="ReadTimeout")
                ],
            },
        }
        result = classify_page(item, page)
        self.assertIsNone(result)

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

    def test_generic_title_with_multiple_live_audio_download_links_is_confirmed(self):
        checks = {
            "results": [
                link("https://yadi.sk/d/audio1", reachable=True),
                link("https://yadi.sk/d/audio2", reachable=True),
                link("https://yadi.sk/d/audio3", reachable=True),
            ]
        }
        result = confirmed_resource_decision(
            "Стрепня от MaraMonstr'а",
            "Музыка и авторские музыкальные композиции. Скачать треки можно по ссылкам.",
            checks,
        )
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "confirmed")

    def test_generic_title_with_only_two_live_links_stays_uncertain(self):
        checks = {
            "results": [
                link("https://yadi.sk/d/audio1", reachable=True),
                link("https://yadi.sk/d/audio2", reachable=True),
            ]
        }
        result = confirmed_resource_decision(
            "Стрепня от MaraMonstr'а",
            "Музыка и авторские музыкальные композиции.",
            checks,
        )
        self.assertIsNone(result)

    def test_legacy_imageshack_image_urls_with_trailing_slash_are_graphics_links(self):
        url = "http://img11.imageshack.us/i/kungfubattler.jpg/"
        live = link(url, reachable=True, text=url)
        live["link_kind"] = "anchor"
        self.assertTrue(is_delivery_link(live, "graphics"))
        self.assertFalse(is_delivery_link(live, "audio"))

        dead = link(url, dead=True, text=url)
        dead["link_kind"] = "anchor"
        self.assertTrue(
            all_delivery_links_dead(
                "battlers i've drawn",
                "I drew these battlers.",
                {"results": [dead]},
            )
        )

    def test_legacy_photobucket_query_filename_is_a_graphics_delivery_link(self):
        url = (
            "http://s395.photobucket.com/albums/pp36/sell58/"
            "?action=view&current=053-Undead03.png"
        )
        candidate = link(url, reachable=True, text=url)
        candidate["link_kind"] = "anchor"
        self.assertTrue(is_delivery_link(candidate, "graphics"))
        # An image URL cannot prove that a music/audio download is available.
        self.assertFalse(is_delivery_link(candidate, "audio"))

    def test_resolved_charset_topic_with_live_photobucket_asset_can_be_confirmed(self):
        url = (
            "http://s395.photobucket.com/albums/pp36/sell58/"
            "?action=view&current=053-Undead03.png"
        )
        candidate = link(url, reachable=True, text=url)
        candidate["link_kind"] = "anchor"
        checks = {"candidate_count": 1, "results": [candidate]}
        result = confirmed_resource_decision(
            "[RESOLVED] Charsets of necromancers and undead.",
            "Reusable charset images are linked in the post.",
            checks,
        )
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "confirmed")

    def test_resolved_marker_does_not_block_live_resource_confirmation(self):
        url = (
            "http://s395.photobucket.com/albums/pp36/sell58/"
            "?action=view&current=053-Undead03.png"
        )
        candidate = link(url, reachable=True, text=url)
        candidate["link_kind"] = "anchor"
        item = {
            "pre_id": "PRE-00364",
            "url": "https://rmrk.net/index.php?topic=30971.0",
            "title": "[RESOLVED] Charsets of necromancers and undead.",
        }
        page = {
            "page_title": item["title"],
            "body_text": "Reusable charset images are linked in the post.",
            "http_status": 200,
            "retrieval_status": "body_found",
            "resource_link_check": {"candidate_count": 1, "results": [candidate]},
        }
        result = classify_page(item, page)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "confirmed")

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


    def test_named_legacy_rmrk_attachment_can_confirm_a_graphic_resource(self):
        url = "https://rmrk.net/index.php?action=dlattach;topic=38714.0;attach=20424"
        candidate = link(url, reachable=True, text="FlameDramon.png")
        candidate["link_kind"] = "image_anchor"

        self.assertTrue(is_delivery_link(candidate, "graphics"))
        self.assertFalse(is_delivery_link(candidate, "audio"))

        result = confirmed_resource_decision(
            "[RMXP] FlameDramon charset",
            "Reusable character charset image attached for use in RPG Maker.",
            {"candidate_count": 1, "results": [candidate]},
        )
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "confirmed")

    def test_legacy_rmrk_preview_attachment_does_not_confirm_resource(self):
        url = "https://rmrk.net/index.php?action=dlattach;topic=38714.0;attach=20424"
        candidate = link(url, reachable=True, text="Screenshot_1-30.png")
        candidate["link_kind"] = "image_anchor"

        self.assertFalse(is_delivery_link(candidate, "graphics"))

    def test_italian_personal_art_topic_ignores_profile_avatar_links(self):
        item = {
            "pre_id": "PRE-00126",
            "url": "https://example.com/topic",
            "title": "My Lavori Pixel Art",
            "review_note": "",
        }
        page = {
            "page_title": "My Lavori Pixel Art",
            "body_text": "A personal pixel-art portfolio and work log.",
            "http_status": 200,
            "retrieval_status": "body_found",
            "resource_link_check": {
                "candidate_count": 1,
                "results": [
                    link(
                        "https://example.com/uploads/profile/photo-thumb-9135.gif",
                        reachable=True,
                        text="Gladiatore79",
                    )
                ],
            },
        }
        result = classify_page(item, page)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "not_applicable")

    def test_moved_topic_without_resource_link_can_be_excluded(self):
        item = {
            "pre_id": "PRE-00331",
            "url": "https://example.com/topic",
            "title": "MOVED: life in the map",
            "review_note": "",
        }
        page = {
            "page_title": "MOVED: life in the map",
            "body_text": "This topic has moved.",
            "http_status": 200,
            "retrieval_status": "body_found",
            "resource_link_check": {
                "candidate_count": 0,
                "results": [],
            },
        }
        result = classify_page(item, page)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "not_applicable")

    def test_moved_resource_topic_with_live_asset_link_is_not_excluded(self):
        item = {
            "pre_id": "PRE-00331",
            "url": "https://example.com/topic",
            "title": "MOVED: Battlers pack",
            "review_note": "",
        }
        page = {
            "page_title": "MOVED: Battlers pack",
            "body_text": "Reusable battler sprites are available at the linked destination.",
            "http_status": 200,
            "retrieval_status": "body_found",
            "resource_link_check": {
                "candidate_count": 1,
                "results": [
                    link(
                        "https://example.com/battlers.zip",
                        reachable=True,
                        text="Battlers download",
                    )
                ],
            },
        }
        result = classify_page(item, page)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "confirmed")


    def test_italian_feedback_only_topic_without_download_is_excluded(self):
        item = {
            "pre_id": "PRE-00124",
            "url": "https://example.com/topic",
            "title": "Icone MZ - stile",
            "review_note": "",
        }
        page = {
            "page_title": "Icone MZ - stile",
            "body_text": "Quale è più carina secondo voi, la uno o la due? Quale preferite?",
            "http_status": 200,
            "retrieval_status": "body_found",
            "resource_link_check": {
                "candidate_count": 1,
                "results": [
                    link(
                        "https://example.com/uploads/profile/photo-thumb-19.jpg",
                        reachable=True,
                        text="Lord Sesshoumaru",
                    )
                ],
            },
        }
        result = classify_page(item, page)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "not_applicable")

    def test_live_download_prevents_request_keyword_from_auto_excluding(self):
        item = {
            "pre_id": "PRE-00189",
            "url": "https://example.com/topic",
            "title": "Looking for sprites",
            "review_note": "",
        }
        page = {
            "page_title": "Looking for sprites",
            "body_text": "Can someone share sprites? I attached the files here.",
            "http_status": 200,
            "retrieval_status": "body_found",
            "resource_link_check": {
                "candidate_count": 1,
                "results": [
                    link(
                        "https://example.com/sprites.zip",
                        reachable=True,
                        text="sprites.zip",
                    )
                ],
            },
        }
        result = classify_page(item, page)
        self.assertIsNone(result)


    def test_invision_thread_collects_reply_downloads_but_ignores_profile_photos(self):
        html = """
        <html><head><title>Icone MZ - stile</title></head><body>
          <div id="ipsLayout_mainArea">
            <div class="cPost_contentWrap">
              <div class="ipsComment_content">
                <div class="ipsType_richText">
                  Which style do you prefer? This is the first post asking for feedback
                  about two icon styles; it does not include a direct download.
                </div>
                <img src="/uploads/profile/photo-thumb-19.jpg" alt="author profile">
              </div>
            </div>
            <div class="cPost_contentWrap">
              <div class="ipsComment_content">
                <div class="ipsType_richText">
                  Here is the reusable icon sheet download.
                  <a href="https://example.com/IconsMZ.zip">Download IconsMZ.zip</a>
                </div>
              </div>
            </div>
          </div>
        </body></html>
        """
        response = Mock()
        response.status_code = 200
        response.url = "https://example.com/topic"
        response.text = html
        response.raise_for_status = Mock()
        session = Mock()
        session.get.return_value = response

        page = parse_html(session, "https://example.com/topic")

        self.assertIn("Which style do you prefer?", page["body_text"])
        self.assertNotIn("reusable icon sheet", page["body_text"])
        urls = {item["url"] for item in page["outbound_links"]}
        self.assertIn("https://example.com/IconsMZ.zip", urls)
        self.assertFalse(any("photo-thumb-19.jpg" in url for url in urls))


    def test_invision_original_post_beats_earlier_recommended_rich_text(self):
        html = """
        <html><head><title>Icone MZ - stile</title></head><body>
          <div class="ipsType_richText">
            Recommended topic: generic resource discussion, not the current post.
          </div>
          <div class="ipsComment_content">
            <div class="ipsType_richText">
              Quale è più carina secondo voi, la uno o la due? Which style do you prefer?
              This post asks for feedback on two icon versions and does not offer a download.
            </div>
          </div>
        </body></html>
        """
        response = Mock()
        response.status_code = 200
        response.url = "https://example.com/topic"
        response.text = html
        response.raise_for_status = Mock()
        session = Mock()
        session.get.return_value = response

        page = parse_html(session, "https://example.com/topic")

        self.assertIn("Quale è più carina", page["body_text"])
        self.assertNotIn("Recommended topic", page["body_text"])

    def test_italian_resource_terms_are_recognized_by_type(self):
        self.assertEqual(resource_kind("Icone MZ - stile", "Which style?"), "graphics")
        self.assertEqual(resource_kind("MIE Musiche", ""), "audio")

    def test_showcase_with_reachable_battler_asset_can_be_confirmed(self):
        checks = {
            "results": [
                {
                    "url": "https://i.imgur.com/battler-sheet.png",
                    "text": "Battler sheet",
                    "link_kind": "image_anchor",
                    "http_status": 200,
                    "dead": False,
                    "reachable": True,
                    "error": None,
                }
            ]
        }
        result = confirmed_resource_decision(
            "My new Battler", "I made this battler; what do you think?", checks
        )
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "confirmed")

    def test_resource_post_with_tutorial_words_and_live_download_can_be_confirmed(self):
        checks = {
            "results": [
                link(
                    "https://example.com/GIF-to-Spritesheet.zip",
                    reachable=True,
                    text="Download source ZIP",
                )
            ]
        }
        result = confirmed_resource_decision(
            "[C#] GIF to Spritesheet",
            "A tutorial explaining how to use the converter. Download the source here.",
            checks,
        )
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "confirmed")


    def test_italian_pixel_art_diaries_without_material_links_are_excluded(self):
        titles = (
            "Imparando Pixel Art & Stuff",
            "Cronache di un pessimo pixel artist",
        )
        for title in titles:
            with self.subTest(title=title):
                item = {
                    "pre_id": "PRE-00125",
                    "url": "https://example.com/topic",
                    "title": title,
                    "review_note": "",
                }
                page = {
                    "page_title": title,
                    "body_text": (
                        "A personal learning diary about improving my own pixel art, "
                        "with progress notes and no downloadable resources."
                    ),
                    "http_status": 200,
                    "retrieval_status": "body_found",
                    "resource_link_check": {
                        "candidate_count": 0,
                        "results": [],
                    },
                }
                result = classify_page(item, page)
                self.assertIsNotNone(result)
                self.assertEqual(result[0], "not_applicable")


if __name__ == "__main__":
    unittest.main()
