import unittest

from sources.community_rpgmaker_it import _is_date_only_title, extract_items


class Rpg2SDateTitleTests(unittest.TestCase):
    def test_date_only_labels_are_rejected(self):
        for title in ("April 3, 2009", "March 7, 2009", "2009-04-03", "3 April 2009"):
            with self.subTest(title=title):
                self.assertTrue(_is_date_only_title(title))

    def test_resource_title_is_kept(self):
        self.assertFalse(_is_date_only_title("Risorse Sonore by GoW"))

    def test_date_link_is_not_collected_as_a_topic_title(self):
        html = """
        <div>
          <a href="/topic/123-sound-pack/">April 3, 2009</a>
          <a href="/topic/124-risorse-sonore/">Risorse Sonore by GoW</a>
        </div>
        """
        items = extract_items(html, section_type="sound")
        self.assertEqual([item["title"] for item in items], ["Risorse Sonore by GoW"])


if __name__ == "__main__":
    unittest.main()
