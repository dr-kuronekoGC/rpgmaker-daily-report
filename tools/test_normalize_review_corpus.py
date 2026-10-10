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


if __name__ == "__main__":
    unittest.main()
