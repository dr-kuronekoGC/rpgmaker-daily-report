from common import (
    load_seen_file,
    save_seen_file,
)

from report import (
    build_report,
    send_to_slack,
)

from sources import (
    community_reddit,
    community_forum,
    official_site,
    official_steam,
    official_opengameart,
    official_kenney,
    official_craftpix,
    official_gamedevmarket,
    official_visustella,
    official_itchio,
    asset_itchio,
)


SOURCES = [
    community_reddit,
    official_site,
    official_steam,
    official_opengameart,
    official_kenney,
    official_craftpix,
    official_gamedevmarket,
    official_visustella,
    official_itchio,
    asset_itchio,
    community_forum,
]


def main():

    all_items = []

    for source in SOURCES:

        try:

            seen = load_seen_file(
                source.SEEN_FILE
            )

            items, new_seen = source.get_items(
                seen
            )

            save_seen_file(
                source.SEEN_FILE,
                new_seen,
            )

            all_items.extend(
                items
            )

        except Exception as e:

            print(
                f"[{source.__name__}] Error: {e}"
            )

    report = build_report(
        all_items
    )

    print()
    print("----- REPORT -----")
    print(report)

    send_to_slack(
        report
    )


if __name__ == "__main__":
    main()
