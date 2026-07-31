# ==========================================
# Steam
# ==========================================

def classify_steam(title):

    title = title.lower()

    if "unite" in title:
        return "UNITE"

    # ------------------------
    # Plugin
    # ------------------------

    plugin_keywords = (

        "plugin",
        "plugins",
        "script",
        "system",
        "engine",
        "tool",
        "builder",
        "generator",

    )

    # ------------------------
    # Material
    # ------------------------

    material_keywords = (

        "asset",
        "assets",
        "tileset",
        "tilesets",
        "music",
        "bgm",
        "sound",
        "audio",
        "portrait",
        "character",
        "faceset",
        "sprite",
        "pixel",
        "battleback",
        "enemy",
        "monster",
        "pack",
        "dlc",

    )

    # ------------------------
    # Game
    # ------------------------

    game_keywords = (

        "game",
        "project",
        "release",
        "released",
        "launch",
        "demo",

    )

    if any(word in title for word in plugin_keywords):
        return "Steamプラグイン"

    if any(word in title for word in material_keywords):
        return "Steam素材"

    if any(word in title for word in game_keywords):
        return "Steamゲーム"

    return "本体ニュース"
