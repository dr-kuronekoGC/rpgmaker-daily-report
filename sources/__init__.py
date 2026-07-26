from . import community_reddit
from . import community_forum

from . import official_site
from . import official_steam

from sources.official_itchio import get_items as itchio

SOURCES = (

    community_reddit,

    official_site,
    official_steam,

    community_forum,

    {
        "name": "itch.io",
        "get_items": itchio,
        "seen_file": "seen_itchio.json",
    },

)
