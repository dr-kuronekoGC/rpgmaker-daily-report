import unittest

from sources.official_raizen import extract_products, normalize_product_url


class OfficialRaizenTests(unittest.TestCase):
    def test_normalizes_only_raizen_product_urls(self):
        self.assertEqual(
            normalize_product_url("/example-plugin?source=creator"),
            "https://raizen884.itch.io/example-plugin",
        )
        self.assertIsNone(
            normalize_product_url("https://example.com/example-plugin")
        )
        self.assertIsNone(normalize_product_url("https://raizen884.itch.io/"))

    def test_extracts_unique_product_cards(self):
        html = """
        <html><body>
          <div class="game_cell">
            <a href="/example-plugin"><span class="game_title">Example Plugin</span></a>
          </div>
          <div class="game_cell">
            <a href="/example-plugin"><span class="game_title">Example Plugin</span></a>
          </div>
          <div class="game_cell">
            <a href="https://example.com/external"><span class="game_title">External</span></a>
          </div>
          <div class="game_cell">
            <a href="/kamigami"><span class="game_title">Kamigami: Clash of the Gods Demo</span></a>
            <div>Mythological Strategic Card Game</div>
          </div>
          <div class="game_cell">
            <a href="/turingy"><span class="game_title">Turingy</span></a>
            <div>Card Game</div>
          </div>
        </body></html>
        """
        items = extract_products(html)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Example Plugin")
        self.assertEqual(items[0]["source"], "Raizen's Plugins")
        self.assertEqual(items[0]["category"], "Raizenプラグイン")


if __name__ == "__main__":
    unittest.main()
