# ==========================================
# itch.io
# ==========================================

def classify_itch(title):

    title = title.lower()

    plugin_keywords = (

        "plugin",
        "tool",
        "system",
        "engine",

    )

    material_keywords = (

        "tileset",
        "sprite",
        "pixel",
        "portrait",
        "character",
        "generator",
        "asset",
        "assets",
        "pack",
        "icon",
        "icons",
        "music",
        "bgm",
        "sound",
        "sfx",
        "audio",
        "ui",
        "gui",
        "animation",
        "battleback",
        "parallax",
        "effects",

    )

    game_keywords = (

        "game",
        "rpg",
        "demo",
        "chapter",
        "episode",

    )

    if any(word in title for word in plugin_keywords):
        return "itchプラグイン"

    if any(word in title for word in material_keywords):
        return "itch素材"

    if any(word in title for word in game_keywords):
        return "itchゲーム"

    # itchは素材サイトなのでデフォルトは素材
    return "itch素材"
