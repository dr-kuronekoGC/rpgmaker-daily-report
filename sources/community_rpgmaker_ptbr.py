"""Collector for RPG Maker-related tools shared in the Brazilian Portuguese forum."""

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from config import RPGMAKER_PTBR_TOOLS_URL, RPGMAKER_PTBR_SEEN_FILE
from sources.base import get_html


SEEN_FILE = RPGMAKER_PTBR_SEEN_FILE
SOURCE_NAME = "Condado Braveheart PT-BR"
BASE_URL = "https://condadobraveheart.com"
QUESTION_MARKERS = (
    "alguém tem", "alguem tem", "alguém conhece", "alguem conhece",
    "como faço", "como faco", "preciso de ajuda", "pedido",
)
RPG_MAKER_MARKERS = (
    "rpg maker", "rpgmaker", "rmmz", "rmmv", "rm2k", "rm2k3",
    "vx ace", "tileset", "plugin",
)
TOOL_MARKERS = (
    "conversor", "converter", "utilitário", "utilitario", "editor",
    "ferramenta", "ferramentas", "software", "plugin", "script",
    "sistema", "programa",
)


def normalize_url(url):
    if not isinstance(url, str) or not url.strip():
        return None
    absolute = urljoin(BASE_URL + "/", url.strip())
    parts = urlparse(absolute)
    if parts.netloc.lower() not in {"condadobraveheart.com", "www.condadobraveheart.com"}:
        return None
    if not re.search(r"/threads/[^/]+\.\d+/?$", parts.path):
        return None
    return f"{BASE_URL}{parts.path}".rstrip("/")


def classify(title):
    text = " ".join(str(title or "").lower().split())
    if not text or any(marker in text for marker in QUESTION_MARKERS):
        return None
    if not any(marker in text for marker in RPG_MAKER_MARKERS):
        return None
    if not any(marker in text for marker in TOOL_MARKERS):
        return None
    if any(marker in text for marker in ("plugin", "script", "sistema")):
        return "Condado PT-BRプラグイン"
    return "Condado PT-BRツール"


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
            "language": "pt",
        })
        local_seen.add(url)
    return items


def get_items(seen):
    if not isinstance(seen, list):
        seen = []
    new_seen = list(seen)
    seen_set = set(seen)
    adopted = []
    try:
        html = get_html(RPGMAKER_PTBR_TOOLS_URL)
    except Exception as exc:
        print(f"[{SOURCE_NAME}] Error: {exc}")
        return [], seen

    for item in extract_items(html):
        url = item["url"]
        if url in seen_set:
            continue
        seen_set.add(url)
        new_seen.append(url)
        adopted.append(item)

    if not seen:
        print(f"[{SOURCE_NAME}] Baseline: {len(new_seen)} items")
        return [], new_seen
    print(f"[{SOURCE_NAME}] New: {len(adopted)}")
    return adopted, new_seen
