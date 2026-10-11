import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from config import (
    RPGMAKER_CN_MZ_URL,
    RPGMAKER_CN_SEEN_FILE,
)
from sources.base import get_html


SEEN_FILE = RPGMAKER_CN_SEEN_FILE
SOURCE_NAME = "Project1 RPG Maker 中文论坛"
MAX_PAGES = 3

QUESTION_MARKERS = (
    "求助", "请问", "請問", "求一个", "求一個", "求推荐", "求推薦",
    "有没有", "有沒有", "怎么做", "如何实现", "如何實現", "为什么",
    "為什麼", "怎么办", "怎麼辦", "求", "寻找", "尋找",
)
PLUGIN_MARKERS = (
    "插件", "脚本", "腳本", "系统", "系統", "战斗", "戰鬥",
    "菜单", "菜單", "ui",
)
GRAPHIC_MARKERS = (
    "素材", "图块", "圖塊", "地图素材", "地圖素材", "立绘", "立繪",
    "行走图", "行走圖", "头像", "頭像", "图标", "圖標", "像素",
)
SOUND_MARKERS = ("音乐", "音樂", "音效", "bgm", "bgs", "se", "音频", "音頻")
TUTORIAL_MARKERS = ("教程", "教学", "教學", "教程", "用法", "制作方法", "製作方法")


def normalize_url(url):
    if not isinstance(url, str) or not url.strip():
        return None
    absolute = urljoin("https://rpg.blue/", url.strip())
    parts = urlparse(absolute)
    if parts.netloc.lower() not in {"rpg.blue", "www.rpg.blue"}:
        return None
    if not re.search(r"/thread-\d+-\d+-\d+\.html$", parts.path):
        return None
    return f"https://rpg.blue{parts.path}"


def classify(title):
    text = " ".join(title.lower().split())
    if any(marker in text for marker in QUESTION_MARKERS):
        return None

    # This is a general MZ board, not every post is a resource.
    # Require clear resource/plugin/tutorial signals and skip showcase-only posts.
    if any(marker in text for marker in SOUND_MARKERS):
        return "Project1中文サウンド素材"
    if any(marker in text for marker in GRAPHIC_MARKERS):
        return "Project1中文グラフィック素材"
    if any(marker in text for marker in PLUGIN_MARKERS):
        return "Project1中文プラグイン"
    if any(marker in text for marker in TUTORIAL_MARKERS):
        return "Project1中文Tips"
    return None


def extract_items(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    local_seen = set()

    for link in soup.select("a[href]"):
        title = link.get_text(" ", strip=True)
        url = normalize_url(link.get("href"))
        if not title or not url or url in local_seen:
            continue

        category = classify(title)
        if category is None:
            continue

        items.append({
            "title": title,
            "url": url,
            "category": category,
            "source": SOURCE_NAME,
            "language": "zh",
        })
        local_seen.add(url)

    return items


def get_next_page_url(html, current_url):
    soup = BeautifulSoup(html, "html.parser")
    for selector in (
        "a.nxt",
        "a[rel='next']",
        "a[href*='forum-627-']",
    ):
        for link in soup.select(selector):
            href = link.get("href")
            if not href:
                continue
            candidate = urljoin(current_url, href)
            if candidate != current_url and "/forum-627-" in candidate:
                return candidate
    return None


def get_items(seen):
    if not isinstance(seen, list):
        seen = []
    new_seen = list(seen)
    seen_set = set(seen)
    adopted = []
    current_url = RPGMAKER_CN_MZ_URL
    visited = set()

    for page in range(1, MAX_PAGES + 1):
        if current_url in visited:
            break
        visited.add(current_url)

        try:
            html = get_html(current_url)
        except Exception as e:
            print(f"[{SOURCE_NAME}] Page {page} error: {e}")
            break

        for item in extract_items(html):
            url = item["url"]
            if url in seen_set:
                continue
            seen_set.add(url)
            new_seen.append(url)
            adopted.append(item)

        next_url = get_next_page_url(html, current_url)
        if not next_url:
            break
        current_url = next_url

    if not seen:
        print(f"[{SOURCE_NAME}] Baseline: {len(new_seen)} items")
        return [], new_seen

    print(f"[{SOURCE_NAME}] New: {len(adopted)}")
    return adopted, new_seen
