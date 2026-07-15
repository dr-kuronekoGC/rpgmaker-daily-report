from config import (
    SEEN_FILE,
    SEEN_OFFICIAL_FILE,
    FORUM_SEEN_FILE,
)

from . import reddit
from . import official
from . import forum

SOURCES = (

    {
        "module": reddit,
        "seen": SEEN_FILE,
    },

    {
        "module": official,
        "seen": SEEN_OFFICIAL_FILE,
    },

    {
        "module": forum,
        "seen": FORUM_SEEN_FILE,
    },

)
