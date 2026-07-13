from . import reddit
from . import official

SOURCES = (
    {
        "module": reddit,
        "seen": "seen.json",
    },
    {
        "module": official,
        "seen": "seen_official.json",
    },
)
