import unittest

from sources.community_rpgmaker_cn import classify, extract_items, normalize_url


class ChineseProject1Tests(unittest.TestCase):
    def test_normalizes_only_discussion_thread_urls(self):
        self.assertEqual(
            normalize_url("/thread-496517-1-1.html"),
            "https://rpg.blue/thread-496517-1-1.html",
        )
        self.assertIsNone(normalize_url("https://example.com/thread-1-1-1.html"))
        self.assertIsNone(normalize_url("/forum-627-1.html"))

    def test_classifies_explicit_resource_and_plugin_signals(self):
        self.assertEqual(
            classify("〖原创发布〗自定义主菜单插件"),
            "Project1中文プラグイン",
        )
        self.assertEqual(
            classify("免费图块素材包"),
            "Project1中文グラフィック素材",
        )
        self.assertEqual(
            classify("战斗音乐与音效"),
            "Project1中文サウンド素材",
        )
        self.assertIsNone(classify("请问有没有好用的插件"))

    def test_extracts_resource_threads_and_skips_questions(self):
        html = """
        <a href="/thread-496517-1-1.html">自定义主菜单插件</a>
        <a href="/thread-496518-1-1.html">免费图块素材包</a>
        <a href="/thread-496519-1-1.html">请问有没有好用的插件</a>
        <a href="/forum-627-1.html">RPG Maker MZ讨论区</a>
        """
        items = extract_items(html)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["language"], "zh")


if __name__ == "__main__":
    unittest.main()
