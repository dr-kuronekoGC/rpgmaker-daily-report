"""Collect resource-related discussions from the Spanish RPG Maker Flarum forum."""

import json

from config import RPGMAKER_ES_API_URL, RPGMAKER_ES_SEEN_FILE
from sources.base import get_html


SEEN_FILE = RPGMAKER_ES_SEEN_FILE
SOURCE_NAME = "Comunidad RPG Maker ES"
BASE_URL = "https://comunidad.rpgmaker.es"
MAX_PAGES = 2

PLUGIN_KEYWORDS = (
    "plugin", "plugins", "complemento", "complementos",
    "script", "scripts",
)
SOUND_KEYWORDS = (
    "audio", "sonido", "sonidos", "música", "musica",
    "bgm", "bgs", "sfx", "efecto de sonido",
)
GRAPHIC_KEYWORDS = (
    "gráfico", "graficos", "gráficos",
    "sprite", "sprites", "tileset", "tilesets", "char",
    "personaje", "personajes", "icono", "iconos", "faceset",
)
TUTORIAL_KEYWORDS = (
    "tutorial", "guía", "guia", "cómo ", "como ",
    "método", "metodo", "comandos", "tips",
)
QUESTION_KEYWORDS = (
    "ayuda", "alguien", "busco", "buscar", "necesito",
    "problema", "problemas", "pregunta", "cómo puedo",
)


def normalize_text(value):
    if not isinstance(value, str):
        return ""
    return " ".join(value.lower().split())


def classify(title, tags=""):
    text = normalize_text(title)
    tag_text = normalize_text(tags)
    combined = f"{text} {tag_text}"

    if any(word in text for word in QUESTION_KEYWORDS):
        return None

    if any(word in combined for word in PLUGIN_KEYWORDS):
        return "Comunidad RPG Maker ESプラグイン"

    if any(word in combined for word in SOUND_KEYWORDS):
        return "Comunidad RPG Maker ESサウンド素材"

    if any(word in combined for word in GRAPHIC_KEYWORDS):
        return "Comunidad RPG Maker ESグラフィック素材"

    if any(word in combined for word in TUTORIAL_KEYWORDS):
        return "Comunidad RPG Maker ESTips"

    return None


def parse_discussions(payload):
    """Return discussion records and the next public API page URL."""
    try:
        document = json.loads(payload)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Flarum API returned invalid JSON") from exc

    data = document.get("data")
    if not isinstance(data, list):
        raise ValueError("Flarum API response has no discussion list")

    included = document.get("included", [])
    tag_names = {
        str(entry.get("id")): str(entry.get("attributes", {}).get("name", ""))
        for entry in included
        if isinstance(entry, dict)
        and entry.get("type") == "tags"
        and entry.get("attributes", {}).get("name")
    }

    discussions = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        attributes = entry.get("attributes") or {}
        title = str(attributes.get("title") or "").strip()
        discussion_id = str(entry.get("id") or "").strip()
        slug = str(attributes.get("slug") or "").strip()
        if not title or not discussion_id:
            continue

        if not slug:
            slug = discussion_id
        url = f"{BASE_URL}/d/{slug}"

        relationships = entry.get("relationships") or {}
        tags_relationship = relationships.get("tags") or {}
        tags_data = tags_relationship.get("data") or []
        tags = " ".join(
            tag_names.get(str(tag.get("id")), "")
            for tag in tags_data
            if isinstance(tag, dict)
        ).strip()

        discussions.append({
            "title": title,
            "url": url,
            "tags": tags,
        })

    links = document.get("links") or {}
    next_url = links.get("next")
    return discussions, next_url if isinstance(next_url, str) and next_url else None


def get_items(seen):
    if not isinstance(seen, list):
        seen = []

    new_seen = list(seen)
    seen_set = set(seen)
    candidates = []
    current_url = RPGMAKER_ES_API_URL
    visited = set()
    pages_fetched = 0
    total_discussions = 0

    while current_url and current_url not in visited and pages_fetched < MAX_PAGES:
        visited.add(current_url)
        try:
            payload = get_html(current_url)
        except Exception as exc:
            # The forum currently returns a 404 for its generated second-page
            # URL in some runs. Keep usable results from earlier pages rather
            # than discarding the entire scan; the shared request tracker still
            # records the failed request, so Source Health can report PARTIAL.
            response = getattr(exc, "response", None)
            status_code = getattr(response, "status_code", None)
            if pages_fetched > 0 and status_code == 404:
                print(
                    f"[{SOURCE_NAME}] Pagination stopped after "
                    f"{pages_fetched} page(s): next page returned HTTP 404"
                )
                break
            raise
        discussions, next_url = parse_discussions(payload)
        pages_fetched += 1
        total_discussions += len(discussions)

        for discussion in discussions:
            url = discussion["url"]
            if url in seen_set:
                continue

            seen_set.add(url)
            new_seen.append(url)
            category = classify(discussion["title"], discussion["tags"])
            if category is None:
                continue

            candidates.append({
                "title": discussion["title"],
                "url": url,
                "category": category,
                "source": SOURCE_NAME,
                "language": "es",
            })

        current_url = next_url

    if pages_fetched == 0:
        raise ValueError("Flarum API returned no pages")
    if total_discussions == 0:
        raise ValueError("Flarum API returned no discussions; refusing an empty scan")

    if not seen:
        print(
            f"[{SOURCE_NAME}] Baseline: {len(new_seen)} discussions "
            f"from {pages_fetched} API page(s)"
        )
        return [], new_seen

    print(
        f"[{SOURCE_NAME}] New: {len(candidates)} resource posts "
        f"from {pages_fetched} API page(s)"
    )
    return candidates, new_seen
