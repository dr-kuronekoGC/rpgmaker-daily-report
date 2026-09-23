# ----------------------------
# Reddit
# ----------------------------

RSS_URL = "https://www.reddit.com/r/RPGMaker/.rss"

# ----------------------------
# Official
# ----------------------------

OFFICIAL_NEWS_URL = "https://rpgmakerofficial.com/news/"

# ----------------------------
# Official Steam
# ----------------------------

OFFICIAL_STEAM_URL = (
    "https://store.steampowered.com/news/"
    "?appgroupname=RPG+Maker+VX"
    "&appids=220700,235900,362870,383730,363890,521880"
    "&feed=steam_community_announcements"
)

OFFICIAL_STEAM_SEEN_FILE = (
    "seen_official_steam.json"
)

# ----------------------------
# Community / Forums
# ----------------------------

FORUM_URL = "https://forums.rpgmakerweb.com/index.php?whats-new/posts/"
RPGMAKERWEB_URL = ""
GUILD_URL = "https://guild.rpgmakerofficial.com/c/14-category/14"
GUILD_PLUGIN_URL = "https://guild.rpgmakerofficial.com/c/14-category/17-category/17"

# ----------------------------
# ツクールフォーラム
# ----------------------------

TKOOL_FORUM_RSS = (
    "https://forum.tkool.jp/index.php?forums/-/index.rss"
)
TKOOL_FORUM_SEEN_FILE = "seen_tkool_forum.json"

# ----------------------------
# Save-Point
# ----------------------------

SAVE_POINT_RSS = (
    "https://www.save-point.org/syndication.php?limit=50"
)
SAVE_POINT_SEEN_FILE = "seen_save_point.json"

# ----------------------------
# RPG Maker Forum DE
# ----------------------------

RPGMAKERFORUM_DE_RSS = (
    "https://rpgmakerforum.de/forum/board-feed/"
)
RPGMAKERFORUM_DE_SEEN_FILE = "seen_rpgmakerforum_de.json"

# ----------------------------
# Chaos Project
# ----------------------------

CHAOS_PROJECT_RESOURCE_URL = (
    "https://forum.chaos-project.com/index.php?board=17.0"
)
CHAOS_PROJECT_SEEN_FILE = "seen_chaos_project.json"

# ----------------------------
# ツクマテ
# ----------------------------

TSUKUMATE_URL = "https://tm.yumineko.com/index.php?f=97"
TSUKUMATE_SEEN_FILE = "seen_tsukumate.json"

# ----------------------------
# ツクプラMZ
# ----------------------------

TSUKUPURA_URL = "https://plugin-mz.fungamemake.com/"
TSUKUPURA_SEEN_FILE = "seen_tsukupura.json"

# ----------------------------
# RPG Maker SU / Нейтральная полоса
# ----------------------------

RPGMAKER_SU_RESOURCE_URL = (
    "https://rpgmaker.su/f70/"
)

RPGMAKER_SU_PLUGIN_URL = (
    "https://rpgmaker.su/f109/"
)

RPGMAKER_SU_SEEN_FILE = (
    "seen_rpgmaker_su.json"
)

# ----------------------------
# 個人サイト / Source Check
# ----------------------------

SOURCE_CHECK_SEEN_FILE = "seen_source_check.json"

SOURCE_CHECK_SITES = [
    {
        "name": "Galv's Plugins",
        "url": "https://galvs-scripts.com/",
    },
    {
        "name": "Atelier RGSS / Moghunter",
        "url": "https://moonglesoft.wordpress.com/",
    },
    {
        "name": "KageDesu Workshop",
        "url": "https://kdworkshop.net/",
    },
    {
        "name": "Blue Coral Games",
        "url": "https://bluecoralgames.com/plugins.php",
    },
    {
        "name": "DK Plugins",
        "url": "https://dk-plugins.ru/mz/dktools/",
    },
    {
        "name": "Hakuen Studio",
        "url": "https://hakuenstudio.itch.io/",
    },
    {
        "name": "Sang Hendrix",
        "url": "https://sanghendrix.itch.io/",
    },
]

# ----------------------------
# seen files
# ----------------------------

REDDIT_SEEN_FILE = "seen.json"
OFFICIAL_SEEN_FILE = "seen_official.json"
FORUM_SEEN_FILE = "seen_forum.json"
RPGMAKERWEB_SEEN_FILE = "seen_rpgmakerweb.json"
GUILD_SEEN_FILE = "seen_guild.json"

# ----------------------------
# HTTP
# ----------------------------

USER_AGENT = "Mozilla/5.0"
REQUEST_TIMEOUT = 30

# ----------------------------
# Slack
# ----------------------------

SLACK_WEBHOOK_ENV = "SLACK_WEBHOOK_URL"

# ==========================================
# itch.io
# ==========================================

ITCHIO_GAME_RSS = (
    "https://itch.io/games/tag-rpgmaker"
)

ITCHIO_ASSET_RSS = (
    "https://itch.io/game-assets/tag-rpg-maker/tag-rpgmaker"
)

ITCHIO_SEEN_FILE = "seen_itchio.json"

# --------------------------------
# OpenGameArt
# --------------------------------

OPENGAMEART_URL = "https://opengameart.org/art-search-advanced"
OPENGAMEART_SEEN_FILE = "seen_opengameart.json"

# ==========================================
# Kenney
# ==========================================

KENNEY_RSS = "https://kenney.nl/assets"
KENNEY_SEEN_FILE = "seen_kenney.json"

# ==========================================
# CraftPix
# ==========================================

CRAFTPIX_RSS = "https://craftpix.net/freebies/"
CRAFTPIX_SEEN_FILE = "seen_craftpix.json"

# ----------------------------
# GameDevMarket
# ----------------------------

GAMEDEVMARKET_URL = (
    "https://www.gamedevmarket.net/category/2d"
)
GAMEDEVMARKET_SEEN_FILE = "seen_gamedevmarket.json"

# ----------------------------
# Maker Devs
# ----------------------------

MAKER_DEVS_URL = (
    "https://makerdevs.com/mz/master-list"
)

MAKER_DEVS_SEEN_FILE = (
    "seen_makerdevs.json"
)

# ----------------------------
# VisuStella
# ----------------------------

VISUSTELLA_URL = "https://visustellamz.itch.io/"
VISUSTELLA_SEEN_FILE = "seen_visustella.json"

# ==========================================
# DeviantArt
# ==========================================

DEVIANTART_SEARCHES = [
    "RPG Maker",
    "RPG Maker MZ",
    "RPG Maker MV",
    "RPG Maker sprites",
    "RPG Maker tileset",
    "RPG Maker assets",
]

DEVIANTART_SEEN_FILE = "seen_deviantart.json"

# ==========================================
# Casper Gaming
# ==========================================

CASPER_RESOURCES_URL = (
    "https://www.caspergaming.com/resources/"
)

CASPER_SOUND_URL = (
    "https://www.caspergaming.com/resources/sound/"
)

CASPER_MAP_URL = (
    "https://www.caspergaming.com/resources/map/"
)

CASPER_PLUGINS_URL = (
    "https://www.caspergaming.com/cgmz/"
)

CASPER_SEEN_FILE = "seen_caspergaming.json"

# ==========================================
# Pending items
# ==========================================

PENDING_ITEMS_FILE = "pending_items.json"

# 1回のSlackレポートに掲載する
# 1サイトあたりの最大件数
MAX_ITEMS_PER_SOURCE = 10

# ==========================================
# triacontane
# ==========================================

TRIACONTANE_REPO_URL = (
    "https://github.com/triacontane/RPGMakerMV"
)

TRIACONTANE_BRANCH = "mz_master"

TRIACONTANE_SEEN_FILE = (
    "seen_triacontane.json"
)
