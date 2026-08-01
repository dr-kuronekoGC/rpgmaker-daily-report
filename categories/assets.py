# ==========================================
# OpenGameArt
# ==========================================

def classify_opengameart(title):

    title = title.lower()

    plugin_keywords = (
        "tool",
        "editor",
        "generator",
    )

    material_keywords = (
        "tileset",
        "tile",
        "sprite",
        "character",
        "portrait",
        "face",
        "battler",
        "icon",
        "icons",
        "ui",
        "gui",
        "background",
        "parallax",
        "animation",
        "effect",
        "pixel",
        "asset",
        "pack",
        "music",
        "bgm",
        "sound",
        "sfx",
        "audio",
        "ambient",
        "rpg",
    )

    if any(word in title for word in plugin_keywords):
        return "OpenGameArtプラグイン"

    if any(word in title for word in material_keywords):
        return "OpenGameArt素材"

    return None


# ==========================================
# Kenney
# ==========================================

def classify_kenney(title):

    title = title.lower()

    plugin_keywords = (
        "tool",
        "editor",
        "generator",
    )

    material_keywords = (
        "asset",
        "pack",
        "tileset",
        "sprite",
        "pixel",
        "ui",
        "icon",
        "music",
        "audio",
        "sound",
        "character",
        "platformer",
        "rpg",
    )

    if any(word in title for word in plugin_keywords):
        return "Kenneyプラグイン"

    if any(word in title for word in material_keywords):
        return "Kenney素材"

    return None


# ==========================================
# CraftPix
# ==========================================

def classify_craftpix(title):

    title = title.lower()

    plugin_keywords = (
        "tool",
        "generator",
    )

    material_keywords = (
        "tileset",
        "sprite",
        "asset",
        "icons",
        "icon",
        "gui",
        "ui",
        "pixel",
        "character",
        "music",
        "audio",
        "sound",
        "pack",
    )

    if any(word in title for word in plugin_keywords):
        return "CraftPixプラグイン"

    if any(word in title for word in material_keywords):
        return "CraftPix素材"

    return None


# ==========================================
# GameDevMarket
# ==========================================

def classify_gamedevmarket(title):

    title = title.lower()

    plugin_keywords = (
        "tool",
        "plugin",
        "editor",
    )

    material_keywords = (
        "asset",
        "tileset",
        "sprite",
        "icon",
        "music",
        "audio",
        "sound",
        "gui",
        "ui",
        "character",
        "pack",
    )

    if any(word in title for word in plugin_keywords):
        return "GameDevMarketプラグイン"

    if any(word in title for word in material_keywords):
        return "GameDevMarket素材"

    return None


# ==========================================
# DeviantArt
# ==========================================

def classify_deviantart(title):

    title = title.lower()

    material_keywords = (
        "tileset",
        "sprite",
        "pixel",
        "rpg maker",
        "asset",
        "character",
        "portrait",
        "faceset",
        "icon",
        "music",
        "sound",
        "pack",
    )

    if any(word in title for word in material_keywords):
        return "DeviantArt素材"

    return None

# ==========================================
# VisuStella
# ==========================================

def classify_visustella(title):

    title = title.lower()

    plugin_keywords = (
        "plugin",
        "tier",
        "core",
        "battle",
        "message",
        "quest",
        "menu",
        "skill",
        "system",
        "update",
        "patch",
    )

    if any(word in title for word in plugin_keywords):
        return "Steamプラグイン"

    return "Steamプラグイン"
