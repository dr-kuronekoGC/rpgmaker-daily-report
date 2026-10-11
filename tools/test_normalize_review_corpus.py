import unittest

from normalize_review_corpus import normalize


def item(title, note, decision="not_applicable", status="resolved"):
    return {
        "pre_id": "PRE-TEST",
        "title": title,
        "review_note": note,
        "decision": decision,
        "status": status,
        "source": "test",
        "url": "https://example.invalid/",
    }


class NormalizeReviewCorpusTests(unittest.TestCase):
    def test_paid_product_exclusion_is_flagged_for_reassessment(self):
        result = normalize(item(
            "[MZ] Example paid plugin",
            "有料プラグインを他サイトで販売する案内のため除外。",
        ))
        self.assertEqual(result["audit_recommendation"], "reassess_paid_policy")
        self.assertIn("paid_policy_changed", result["flags"])

    def test_time_limited_sale_is_not_mistaken_for_paid_product_only(self):
        result = normalize(item(
            "Free Plugin Giveaway",
            "プラグインのタイムセール告知。期間限定の一時的な情報のため登録不要。",
        ))
        self.assertEqual(result["audit_recommendation"], "reassess_promotion")

    def test_confirmed_free_asset_is_an_include_candidate(self):
        result = normalize(item(
            "Free sprite sheet",
            "キャラクターセット。公開対象。",
            decision="confirmed",
        ))
        self.assertEqual(result["audit_recommendation"], "include_candidate")

    def test_deleted_post_is_marked_unavailable_not_non_asset(self):
        result = normalize(item(
            "A resource post",
            "投稿削除済みで本文を確認できないため登録不要。",
        ))
        self.assertEqual(result["audit_recommendation"], "exclude_unavailable")
        self.assertIn("content_unavailable", result["flags"])

    def test_duplicate_is_separated_from_general_plugin_exclusion(self):
        result = normalize(item(
            "Plugin tool",
            "PRE-00093と同じ内容との確認あり。重複として除外。",
        ))
        self.assertEqual(result["audit_recommendation"], "exclude_duplicate")

    def test_individual_preference_is_flagged_without_becoming_global_rule(self):
        result = normalize(item(
            "[F2U] Sprite Base",
            "グラフィック素材。ただし個人的な好みによる判断で今回は公開対象外。",
            decision="confirmed",
        ))
        self.assertIn("individual_editorial_exception", result["flags"])
        self.assertEqual(result["audit_recommendation"], "include_candidate")

    def test_open_uncertain_case_remains_review(self):
        result = normalize(item(
            "Unclear resource",
            "詳細を確認できず判断保留。",
            status="open",
        ))
        self.assertEqual(result["audit_recommendation"], "needs_review")
        self.assertIn("still_open", result["flags"])

    def test_premiere_discussion_about_sprite_sizes_is_excluded(self):
        result = normalize(item(
            "Sprite sizes for a SNES style game",
            "素材・プラグイン・制作支援ツールの紹介ではなく、ファミコン／スーパーファミコン版『ファイナルファンタジー』のドットサイズについての雑談・質問。収集対象外。",
        ))
        self.assertEqual(result["audit_recommendation"], "exclude_discussion")
        self.assertIn("question_discussion_or_chat", result["purpose_labels"])


    def test_game_system_showcase_is_not_treated_as_a_developer_tool(self):
        result = normalize(item(
            "Hoverable Tool Tips!!!",
            "ゲームシステムの紹介であり、素材ではない。",
        ))
        self.assertEqual(result["audit_recommendation"], "exclude_showcase")
        self.assertIn("game_showcase_or_process", result["purpose_labels"])

    def test_plugin_intro_movie_is_a_showcase_not_a_released_plugin(self):
        result = normalize(item(
            "RPG Maker MZ - 3D Plugin",
            "プラグイン紹介のムービー。今回は除外。",
        ))
        self.assertEqual(result["audit_recommendation"], "exclude_showcase")

    def test_announcement_without_distribution_is_out_of_scope(self):
        result = normalize(item(
            "Sprite Replacement",
            "素材配布ではなく、お知らせ・告知と判断したため除外。",
        ))
        self.assertEqual(result["audit_recommendation"], "exclude_out_of_scope")
        self.assertIn("announcement_or_revision_without_deliverable", result["purpose_labels"])

    def test_unreadable_language_stays_in_manual_review(self):
        result = normalize(item(
            "Что, где, куда и как?",
            "素材なし。ロシア語で内容を判読できないため除外。",
        ))
        self.assertEqual(result["audit_recommendation"], "needs_review")
        self.assertIn("language_review", result["flags"])


    def test_negative_material_distribution_phrase_does_not_override_discussion_exclusion(self):
        result = normalize(item(
            "Quick Asset information & Finding Resources | Tips For New Devs",
            "素材についての雑談・議論であり、具体的な素材配布情報ではないため除外。",
        ))
        self.assertEqual(result["audit_recommendation"], "exclude_discussion")

    def test_explicitly_negative_distribution_is_not_positive_evidence(self):
        result = normalize(item(
            "Musiche originali",
            "雑談。素材を配布していないため、素材配布・有用な制作支援情報ではない。",
        ))
        self.assertEqual(result["audit_recommendation"], "exclude_discussion")

    def test_original_material_distribution_negative_is_excluded(self):
        result = normalize(item(
            "Some sprites & tiles I made for a game I'm working on.",
            "自作素材のサンプル画面紹介で、素材配布そのものではないため除外。",
        ))
        self.assertEqual(result["audit_recommendation"], "exclude_preview")

    def test_reusable_source_data_boundary_stays_in_review(self):
        result = normalize(item(
            "This 2.5D tool is crazy!",
            "2.5Dの画面を作成し、生のデータファイルを提供。素材そのものではないが、参考・再利用価値のある境界例。",
        ))
        self.assertEqual(result["audit_recommendation"], "needs_review")
        self.assertIn("reusable_source_data_boundary", result["purpose_labels"])
        self.assertIn("reusable_deliverable_review", result["flags"])

    def test_character_creation_process_video_is_showcase(self):
        result = normalize(item(
            "Guys i swear im locked in i wanted to show my process for making characters its pencil and paper lol",
            "制作過程を紹介する動画であり、再利用可能な素材の配布ではないため除外。",
        ))
        self.assertEqual(result["audit_recommendation"], "exclude_showcase")

    def test_confirmed_developer_tool_is_not_excluded_by_generic_preview_wording(self):
        result = normalize(item(
            "[Tool] Browser-based .rmmzsave editor",
            "セーブデータを調整・編集できる無料ツール。素材そのものではないが、制作支援ツールとして採用。",
            decision="confirmed",
        ))
        self.assertEqual(result["audit_recommendation"], "include_candidate")
        self.assertIn("developer_tool", result["purpose_labels"])


if __name__ == "__main__":
    unittest.main()
