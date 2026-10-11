import feedparser

from config import (
    RPGMAKER_ES_RSS,
    RPGMAKER_ES_SEEN_FILE,
)

SEEN_FILE = RPGMAKER_ES_SEEN_FILE
SOURCE_NAME = "Comunidad RPG Maker ES"

PLUGIN_KEYWORDS = (
    "plugin", "plugins", "complemento", "complementos",
    "script", "scripts", "mz", "mv", "200x",
)
SOUND_KEYWORDS = (
    "audio", "sonido", "sonidos", "música", "musica",
    "bgm", "bgs", "sfx", "efecto de sonido",
)
GRAPHIC_KEYWORDS = (
    "recurso", "recursos", "gráfico", "graficos", "gráficos",
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


def get_tags(entry):
    tags = []
    for tag in entry.get("tags", []):
        if isinstance(tag, dict) and tag.get("term"):
            tags.append(str(tag["term"]))
    for category in entry.get("categories", []):
        if isinstance(category, str):
            tags.append(category)
    return " ".join(tags)


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


def get_items(seen):
    if not isinstance(seen, list):
        seen = []

    try:
        feed = feedparser.parse(RPGMAKER_ES_RSS)
        new_seen = list(seen)
        seen_set = set(seen)
        candidates = []

        for entry in feed.entries:
            url = entry.get("link")
            title = entry.get("title", "").strip()
            if not url or not title or url in seen_set:
                continue

            tags = get_tags(entry)
            category = classify(title, tags)
            new_seen.append(url)
            seen_set.add(url)

            if category is None:
                continue

            candidates.append({
                "title": title,
                "url": url,
                "category": category,
                "source": SOURCE_NAME,
                "language": "es",
            })

        if not seen:
            print(f"[{SOURCE_NAME}] Baseline: {len(new_seen)} items")
            return [], new_seen

        print(f"[{SOURCE_NAME}] New: {len(candidates)}")
        return candidates, new_seen

    except Exception as e:
        print(f"[{SOURCE_NAME}] Error: {e}")
        return [], seen
