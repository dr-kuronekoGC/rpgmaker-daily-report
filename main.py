from common import (
    load_seen_file,
    save_seen_file,
)

from report import (
    build_report,
    send_to_slack,
)

from sources import SOURCES


def main():

    all_items = []

    for source in SOURCES:

        seen = load_seen_file(
            source["seen"]
        )

        items, new_seen = (
            source["module"].get_items(seen)
        )

        save_seen_file(
            source["seen"],
            new_seen,
        )

        all_items.extend(items)

    report = build_report(all_items)

    print()
    print("----- REPORT -----")
    print(report)

    send_to_slack(report)


if __name__ == "__main__":
    main()
