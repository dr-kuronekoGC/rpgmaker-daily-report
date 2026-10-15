# ==========================================
# Asset Classification
# ==========================================

from .keywords import (
    GRAPHIC_KEYWORDS,
    SOUND_KEYWORDS,
    PLUGIN_KEYWORDS,
)


# ==========================================
# Strong keywords
# ==========================================

STRONG_SOUND_KEYWORDS = (
    "music",
    "bgm",
    "sound",
    "sfx",
    "audio",
    "soundtrack",
    "ost",
)


# 「これがタイトルやタグにあれば、
# 素材そのものの可能性が高い」キーワード。
STRONG_GRAPHIC_KEYWORDS = (
    "sprite",
    "sprites",
    "tileset",
    "tilesets",
    "tile set",
    "tilemap",
    "character",
    "characters",
    "portrait",
    "portraits",
    "faceset",
    "face set",
    "icon",
    "icons",
    "background",
    "backgrounds",
    "texture",
    "textures",
    "pixel art",
    "pixelart",
    "pixel-art",
    "ui",
    "user interface",
)

DEVIANTART_RESOURCE_KEYWORDS = (
    "asset",
    "assets",
    "resource",
    "resources",
    "sprite",
    "sprites",
    "spritesheet",
    "tileset",
    "tilesets",
    "tilesheet",
    "icon",
    "icons",
    "faceset",
    "portrait",
    "generator",
    "generatorpart",
    "generatorparts",
    "charset",
    "character sheet",
    "character base",
    "map",
    "map pack",
    "parallax",
    "background",
    "overlay",
)

# ==========================================
# Map / Parallax
# ==========================================
#
# map / mapping / parallax は、
# 「素材」ではなく「作品・作例」の場合が多い。
#
# そのため、これらだけでは
# グラフィック素材と判定しない。
#
# pack / asset / resource / download などと
# 組み合わさった場合のみ素材候補とする。
# ==========================================

MAP_KEYWORDS = (
    "map",
    "maps",
    "mapping",
    "mapmaking",
    "parallax",
    "parallax mapping",
    "parallaxmap",
)


MAP_CONTEXT_KEYWORDS = (
    "map pack",
    "map set",
    "map collection",
    "map bundle",
    "map resource",
    "map resources",
    "map asset",
    "map assets",
    "parallax pack",
    "parallax set",
    "parallax collection",
    "parallax bundle",
    "parallax resource",
    "parallax resources",
    "parallax asset",
    "parallax assets",
    "downloadable map",
    "downloadable maps",
    "downloadable parallax",
    "free map",
    "free maps",
    "free parallax",
)

# ==========================================
# Pack / bundle keywords
# ==========================================

PACK_KEYWORDS = (
    "asset pack",
    "asset bundle",
    "resource pack",
    "resource bundle",
    "graphics pack",
    "graphic pack",
    "sprite pack",
    "sprite bundle",
    "tileset pack",
    "tileset bundle",
    "tileset collection",
    "tileset set",
    "icon pack",
    "icon set",
    "character pack",
    "character set",
    "faceset pack",
    "faceset set",
    "background pack",
    "background set",
    "ui pack",
    "ui set",
)


# ==========================================
# Asset size / pack keywords
# ==========================================

LARGE_PACK_KEYWORDS = (
    "mega pack",
    "megapack",
    "mega-pack",
    "ultimate pack",
    "ultimate bundle",
    "complete pack",
    "complete bundle",
    "full pack",
    "full set",
    "massive pack",
    "large pack",
    "big pack",
    "huge pack",
    "asset pack",
    "asset bundle",
    "sprite pack",
    "sprite sheet pack",
    "tileset pack",
    "tileset collection",
    "icon pack",
    "icon set",
    "character pack",
    "character set",
    "faceset pack",
    "faceset set",
)


# ==========================================
# Fan work / derivative work
# ==========================================

FANWORK_KEYWORDS = (
    "fanart",
    "fan art",
    "fan-game",
    "fan game",
    "fangame",
    "crossover",
    "tribute",
    "pokemon",
    "mario",
    "zelda",
    "final fantasy",
    "dragon quest",
    "kingdom hearts",
    "disney",
    "marvel",
    "dc comics",
    "sonic",
    "kirby",
    "undertale",
    "fate",
    "genshin",
)


# ==========================================
# Official edit / RTP edit
# ==========================================

OFFICIAL_EDIT_KEYWORDS = (
    "rtp edit",
    "rtp edits",
    "official edit",
    "official edits",
    "rpg maker edit",
    "rpg maker edits",
    "mv rtp edit",
    "mz rtp edit",
    "vx ace rtp edit",
    "vx rtp edit",
)


# ==========================================
# RPG Maker specific keywords
# ==========================================

RPGMAKER_KEYWORDS = (
    "rpg maker",
    "rpgmaker",
    "rpg-maker",
    "rpgmaker mv",
    "rpgmaker mz",
    "rpg maker mv",
    "rpg maker mz",
    "rpgmakermv",
    "rpgmakermz",
)


# ==========================================
# Keywords suggesting a showcase / example
# ==========================================
#
# これらは単独では「素材ではない」と断定しない。
# ただし map / parallax と組み合わさった場合、
# 作例である可能性を高く見る。
# ==========================================

SHOWCASE_KEYWORDS = (
    "screenshot",
    "showcase",
    "showcasing",
    "practice",
    "map practice",
    "level design",
    "leveldesign",
    "game design",
    "gamedesign",
    "gameplay",
    "in-game",
    "ingame",
    "work in progress",
    "wip",
)
# ==========================================
# DeviantArt project / showcase keywords
# ==========================================
#
# 「自作ゲームの制作物・作例」である可能性を
# 示すキーワード。
#
# 素材全体には適用せず、
# map / parallax の判定に限定して使用する。
# ==========================================

DEVIANTART_PROJECT_KEYWORDS = (
    "my game",
    "my project",
    "my rpg",
    "my rpg maker",
    "my independent project",
    "my own game",
    "my own project",
    "working on",
    "working on my",
    "made on rpg maker",
    "made in rpg maker",
    "created in rpg maker",
    "for my game",
    "for my project",
    "game i'm working on",
    "project i'm working on",
    "development",
    "devlog",
    "first town",
    "second town",
    "third town",
)

# ==========================================
# DeviantArt resource / distribution keywords
# ==========================================
#
# 作品紹介らしい説明があっても、
# 実際に素材として配布・利用できることを示す
# 記述があれば、素材として残す。
# ==========================================

DEVIANTART_DISTRIBUTION_KEYWORDS = (
    "free to use",
    "free for use",
    "free resource",
    "free resources",
    "use in your project",
    "use in your projects",
    "use for your project",
    "use for your projects",
    "you can use",
    "can be used in your project",
    "commercial use",
    "non-commercial use",
    "non commercial use",
    "credit required",
    "credit me",
    "please credit",
    "credits required",
    "free download for your project",
    "downloadable resource",
    "downloadable resources",
    "asset pack",
    "resource pack",
)
