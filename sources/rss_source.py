from sources.rss import collect_rss


def collect_rss_items(
    rss_url,
    seen,
    classifier,
    source_name,
):
    """
    後方互換用

    新規処理ではcollect_rssを使用する
    """

    return collect_rss(
        url=rss_url,
        seen=seen,
        classify=classifier,
        source_name=source_name,
    )
