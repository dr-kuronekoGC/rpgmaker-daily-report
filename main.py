from common import (
    load_seen_file,
    save_seen_file,
)

from report import (
    build_report,
    send_to_slack,
)

from config import (
    SEEN_FILE,
    SEEN_OFFICIAL_FILE,
)

import sources.reddit as reddit
import sources.official as official


# ==========================================
# Sources
# ==========================================

SOURCES = [

    {
        "module": reddit,
        "seen": SEEN_FILE,
    },

    {
        "module": official,
        "seen": SEEN_OFFICIAL_FILE,
    },

]


# ==========================================
# Main
# ==========================================

def main():

    all_items = []

    for source in SOURCES:

        seen = load_seen_file(
            source["seen"]
        )

        items, seen = (
            source["module"].get_items(seen)
        )

        all_items.extend(items)

        save_seen_file(
            source["seen"],
            seen,
        )

    report = build_report(all_items)

    print()
    print("----- REPORT -----")
    print(report)

    send_to_slack(report)


if __name__ == "__main__":

    main()
