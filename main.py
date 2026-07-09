from common import (
    load_seen,
    load_seen_file,
    save_seen,
    save_seen_file,
)

from config import SEEN_OFFICIAL_FILE

from report import (
    build_report,
    send_to_slack,
)

import reddit_source
import official_source


def main():

    # Reddit
    reddit_seen = load_seen()

    reddit_items, reddit_seen = (
        reddit_source.get_reddit_items(
            reddit_seen
        )
    )

    # Official
    official_seen = load_seen_file(
        SEEN_OFFICIAL_FILE
    )

    official_items, official_seen = (
        official_source.get_official_news_items(
            official_seen
        )
    )

    # 収集結果をまとめる
    items = (
        reddit_items
        + official_items
    )

    # seen保存
    save_seen(reddit_seen)

    save_seen_file(
        SEEN_OFFICIAL_FILE,
        official_seen,
    )

    # レポート作成
    report = build_report(items)

    print()
    print("----- REPORT -----")
    print(report)

    # Slack送信
    send_to_slack(report)


if __name__ == "__main__":
    main()
