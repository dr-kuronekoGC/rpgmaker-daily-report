from common import (
    load_seen_file,
    save_seen_file,
)

from config import (
    SEEN_FILE,
    SEEN_OFFICIAL_FILE,
)

from report import (
    build_report,
    send_to_slack,
)

from sources import reddit
from sources import official


SOURCES = (
    (reddit, SEEN_FILE),
    (official, SEEN_OFFICIAL_FILE),
)


def collect_all_items():

    all_items = []

    for module, seen_file in SOURCES:

        seen = load_seen_file(seen_file)

        items, new_seen = module.get_items(seen)

        save_seen_file(
            seen_file,
            new_seen,
        )

        all_items.extend(items)

    return all_items


def main():

    items = collect_all_items()

    report = build_report(items)

    print()
    print("----- REPORT -----")
    print(report)

    send_to_slack(report)


if __name__ == "__main__":
    main()
