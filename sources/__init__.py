from . import community_reddit
from . import community_forum

from . import official_site
from . import official_steam
from . import official_opengameart
from . import official_kenney
from . import official_craftpix
from . import official_gamedevmarket

from sources.asset_itchio import get_items as itchio

SOURCES = (

    community_reddit,

    official_site,
    official_steam,
    official_opengameart,
    official_kenney,
    official_craftpix,

    community_forum,

    {
        "name": "itch.io",
        "get_items": itchio,
        "seen_file": "seen_itchio.json",
    },

)
