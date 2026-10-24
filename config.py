# ----------------------------
# Reddit
# ----------------------------

RSS_URL = "https://www.reddit.com/r/RPGMaker/.rss"

# ----------------------------
# Official
# ----------------------------

OFFICIAL_NEWS_URL = "https://rpgmakerofficial.com/news/"

# Stable links to official RPG Maker announcements and social channels.
# These are shown in every Slack report, even when no new items were found.
OFFICIAL_INFORMATION_LINKS = (
    ("公式ニュース", "https://rpgmakerofficial.com/news/"),
    ("ツクール開発部 公式X（最新投稿）", "https://x.com/tkool_dev"),
    ("U2U公式X（日本語・最新投稿）", "https://x.com/rpgmakeru2u_jp"),
    ("U2U公式X（英語・最新投稿）", "https://x.com/rpgmakeru2u_en"),
    ("公式フォーラム", "https://forum.tkool.jp/"),
    ("公式YouTube", "https://www.youtube.com/@GotchaGotchaGames"),
    ("公式Discord", "https://discord.gg/8TZDDgPked"),
)

# ----------------------------
# Steam Workshop resources (separate from Steam news)
# ----------------------------

STEAM_WORKSHOP_SEEN_FILE = "seen_steam_workshop.json"
STEAM_WORKSHOP_QUERIES = (
    ("プラグイン", "https://steamcommunity.com/workshop/browse/?appid=1096900&browsesort=mostrecent&section=readytouseitems&requiredtags%5B%5D=Plugins"),
    ("グラフィック素材", "https://steamcommunity.com/workshop/browse/?appid=1096900&browsesort=mostrecent&section=readytouseitems&requiredtags%5B%5D=Tilesets"),
    ("音楽素材", "https://steamcommunity.com/workshop/browse/?appid=1096900&browsesort=mostrecent&section=readytouseitems&requiredtags%5B%5D=Music"),
    ("効果音素材", "https://steamcommunity.com/workshop/browse/?appid=1096900&browsesort=mostrecent&section=readytouseitems&requiredtags%5B%5D=Sound%20Effects"),
    ("素材パック", "https://steamcommunity.com/workshop/browse/?appid=1096900&browsesort=mostrecent&section=readytouseitems&requiredtags%5B%5D=Pack"),
)

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
# RPG Maker Union
# ----------------------------

RPGMAKER_UNION_RESOURCE_URL = (
    "https://rpgmakerunion.ru/forum/resursy.16"
)

RPGMAKER_UNION_PLUGIN_URL = (
    "https://rpgmakerunion.ru/forum/plaginy-i-skripty.15"
)

RPGMAKER_UNION_SEEN_FILE = (
    "seen_rpgmaker_union.json"
)

# ----------------------------
# Oniromancie / RPG-MAKER.FR
# ----------------------------

ONIROMANCIE_SCRIPTS_URL = (
    "https://www.rpg-maker.fr/index.php?page=scripts"
)

ONIROMANCIE_SEEN_FILE = (
    "seen_oniromancie.json"
)

# ----------------------------
# 個人サイト / Source Check
# ----------------------------

SOURCE_CHECK_SEEN_FILE = "seen_source_check.json"

SOURCE_CHECK_SITES = [
    {
        "name": "Galv's Plugins",
        "url": "https://galvs-scripts.com/",
        "resource_types": ["プラグイン"],
        "language": "英語中心",
        "site_type": "プラグイン配布サイト",
    },
    {
        "name": "Atelier RGSS / Moghunter",
        "url": "https://moonglesoft.wordpress.com/",
        "resource_types": ["プラグイン"],
        "language": "ポルトガル語中心（英訳がある作品もあり）",
        "site_type": "プラグイン配布サイト",
    },
    {
        "name": "KageDesu Workshop",
        "url": "https://kdworkshop.net/",
        "resource_types": ["プラグイン"],
        "language": "英語・ロシア語",
        "site_type": "プラグイン配布サイト",
    },
    {
        "name": "Blue Coral Games",
        "url": "https://bluecoralgames.com/plugins.php",
        "resource_types": ["プラグイン"],
        "language": "英語中心",
        "site_type": "プラグイン配布サイト",
    },
    {
        "name": "DK Plugins",
        "url": "https://dk-plugins.ru/mz/dktools/",
        "resource_types": ["プラグイン"],
        "language": "英語・ロシア語",
        "site_type": "プラグイン配布サイト",
    },
    {
        "name": "Hakuen Studio",
        "url": "https://hakuenstudio.itch.io/",
        "resource_types": ["プラグイン"],
        "language": "英語中心",
        "site_type": "プラグイン配布サイト",
    },
    {
        "name": "Sang Hendrix",
        "url": "https://sanghendrix.itch.io/",
        "resource_types": ["プラグイン"],
        "language": "英語中心（日本語対応プラグインあり）",
        "site_type": "プラグイン配布サイト",
    },
    {
        "name": "Raizen Plugins",
        "url": "https://raizen884.itch.io/",
        "resource_types": ["プラグイン"],
        "language": "英語中心（コメント欄は多言語）",
        "site_type": "プラグイン配布サイト",
    },
    {
        "name": "GameDevMarket",
        "url": "https://www.gamedevmarket.net/category/2d",
        "resource_types": ["グラフィック素材"],
        "language": "英語（サイト表示は英語のみ）",
        "site_type": "マーケットプレイス",
        "reference_only": True,
    },
    {
        "name": "Maker Devs",
        "url": "https://makerdevs.com/mz/master-list",
        "resource_types": ["プラグイン"],
        "language": "英語中心（掲載プラグインにより異なる）",
        "site_type": "プラグイン一覧",
        "reference_only": True,
    },
    {
        "name": "RPG Refuge（2D素材フォーラム）",
        "url": "https://rpg-refuge.com/forums/2d-assets.57/",
        "alternate_feed_url": "https://rpg-refuge.com/forums/2d-assets.57/index.rss",
        "resource_types": ["グラフィック素材"],
        "language": "英語中心（投稿者により多言語）",
        "site_type": "掲示板・コミュニティ",
        "reference_only": True,
    },
    {
        "name": "New RPG Project",
        "url": "https://newrpg.seesaa.net/",
        "alternate_feed_url": "https://newrpg.seesaa.net/index20.rdf",
        "resource_types": ["プラグイン", "開発ツール"],
        "language": "日本語",
        "site_type": "個人サイト・プラグイン配布",
        "reference_only": True,
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

# ==========================================
# RPG Maker Web - International Resources Blog
# ==========================================

RPGMAKERWEB_BLOG_URL = "https://www.rpgmakerweb.com/category/resources"
RPGMAKERWEB_BLOG_SEEN_FILE = "seen_rpgmakerweb_blog.json"

# ==========================================
# Raizen's RPG Maker Plugins
# ==========================================

RAIZEN_PLUGINS_URL = "https://raizen884.itch.io/"
RAIZEN_PLUGINS_SEEN_FILE = "seen_raizen_plugins.json"


# ----------------------------
# International community forums
# ----------------------------

RPGMAKER_ES_API_URL = "https://comunidad.rpgmaker.es/api/discussions?include=tags&page%5Blimit%5D=50&sort=-lastPostedAt"
RPGMAKER_ES_SEEN_FILE = "seen_rpgmaker_es.json"

RPGMAKER_FR_RESOURCE_URL = "https://forum.rpgmakervx-fr.com/f118-ressources"
RPGMAKER_FR_SEEN_FILE = "seen_rpgmaker_fr.json"

# ----------------------------
# Project1 / Chinese RPG Maker community
# ----------------------------

RPGMAKER_CN_MZ_URL = "https://rpg.blue/forum-627-1.html"
RPGMAKER_CN_SEEN_FILE = "seen_rpgmaker_cn.json"

# ----------------------------
# Russian RPG Maker community
# ----------------------------

RPGMAKER_RU_PLUGIN_URL = "https://rpgmaker.ru/forum/u-mz"
RPGMAKER_RU_GRAPHICS_URL = "https://rpgmaker.ru/forum/grafika/"
RPGMAKER_RU_MUSIC_URL = "https://rpgmaker.ru/forum/muzyka/"
RPGMAKER_RU_SEEN_FILE = "seen_rpgmaker_ru.json"

# ----------------------------
# Brazilian Portuguese game-dev community
# ----------------------------

RPGMAKER_PTBR_TOOLS_URL = "https://condadobraveheart.com/forums/programas-utilitarios.184/"
RPGMAKER_PTBR_SEEN_FILE = "seen_rpgmaker_ptbr.json"

# ----------------------------
# Italian RPG Maker community
# ----------------------------

RPGMAKER_IT_FORUM_HOME = "https://www.rpg2s.it/forum/"
RPGMAKER_IT_MZ_PLUGIN_URL = "https://www.rpg2s.it/forum/index.php?/forum/146-plugin-e-j097v097script/"
RPGMAKER_IT_MV_PLUGIN_URL = "https://www.rpg2s.it/forum/index.php?/forum/131-plugin-e-j097v097script/"
RPGMAKER_IT_SEEN_FILE = "seen_rpgmaker_it.json"

# ----------------------------
# Additional international resource forums
# ----------------------------

# RM Planet (XenForo public RSS feed)
RMPLANET_RSS = "https://forum.rmplanet.com/forums/-/index.rss"
RMPLANET_SEEN_FILE = "seen_rmplanet.json"

# Makerando (Italian RPG Maker forum)
MAKERANDO_FORUM_URL = "https://www.makerando.com/forum/"
MAKERANDO_SEEN_FILE = "seen_makerando.json"


# ----------------------------
# RPG Refuge community forum
# ----------------------------

RPG_REFUGE_SEEN_FILE = "seen_rpg_refuge.json"

# ----------------------------
# Additional resource forums
# ----------------------------

# RMRK: historical resource database; prioritize archival collection.
RMRK_RESOURCE_URL = "https://rmrk.net/index.php?board=114.0"
RMRK_SEEN_FILE = "seen_rmrk.json"

# RPG Maker Network (RMN)
RPGMAKER_NET_RESOURCES_URL = "https://rpgmaker.net/resources/"
RPGMAKER_NET_SEEN_FILE = "seen_rpgmaker_net.json"

# ----------------------------
# GameBanana RPG Maker resource communities (public RSS API)
# ----------------------------
# The RSS endpoint accepts one gameid per request (unlike Core/List/New).
# Query MV and MZ separately; request the maximum documented RSS page size.
GAMEBANANA_RSS_URLS = (
    "https://api.gamebanana.com/Rss/New?gameid=5758&perpage=50",
    "https://api.gamebanana.com/Rss/New?gameid=13221&perpage=50",
)
GAMEBANANA_SEEN_FILE = "seen_gamebanana.json"
