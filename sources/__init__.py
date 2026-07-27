from . import community_reddit
from . import community_forum

from . import official_site
from . import official_steam
from . import official_itchio
from . import official_opengameart

SOURCES = (
    official_site,
    official_steam,
    official_itchio,
    official_opengameart,

    community_forum,
    community_reddit,
)
