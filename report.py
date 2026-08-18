import os
import requests

from common import (
    now_jst,
    get_period,
)

from config import (
    REQUEST_TIMEOUT,
    SLACK_WEBHOOK_ENV,
)

from categories import DISPLAY_CATEGORY


# ==========================================
# Category Display
# ==========================================

CATEGORY_GROUPS = {
    "★★★★★ 今日の注目": [
        "本体ニュース",
        "UNITE",
        "Forum重要事項",
    ],

    "★★★★☆ 新作ゲーム": [
        "ゲーム",
    ],

    "★★★☆☆ プラグイン・素材": [
        "プラグイン",
        "素材",
    ],

    "★★☆☆☆ 開発情報・Tips": [
        "Tips",
    ],

    "★☆☆☆☆ 質問・相談": [
        "質問",
    ],
}


DISPLAY_ORDER = [
    "本体ニュース",
    "UNITE",
    "Forum重要事項",
    "プラグイン",
    "素材",
    "ゲーム",
    "Tips",
    "質問",
]


# ==========================================
# Category Helpers
# ==========================================

def get_display_category(category):

    """
    内部カテゴリをSlack表示用カテゴリへ変換する。
    """

    info = DISPLAY_CATEGORY.get(
        category
    )

    if isinstance(info, dict):

        group = info.get(
            "group"
        )

        if group == "グラフィック素材":
            return "グラフィック素材"

        if group == "サウンド素材":
            return "サウンド素材"

        if group == "プラグイン":
            return "プラグイン"

        if group == "ゲーム":
            return "ゲーム"

        if group == "Tips":
            return "Tips"

        if group == "質問":
            return "質問"

        if group == "公式":
            return category

    return category


def get_report_group(category):

    """
    サマリー表示用の大分類を返す。
    """

    display_category = get_display_category(
        category
    )

    if display_category in (
        "プラグイン",
        "グラフィック素材",
        "サウンド素材",
    ):
        return "プラグイン・素材"

    if display_category == "ゲーム":
        return "新作ゲーム"

    if display_category == "Tips":
        return "開発情報・Tips"

    if display_category == "質問":
        return "質問・相談"

    if display_category in (
        "本体ニュース",
        "UNITE",
        "Forum重要事項",
    ):
        return "今日の注目"

    return None


# ==========================================
# DeviantArt Detail
# ==========================================

def format_deviantart_detail(
    item,
):
    """
    DeviantArtから取得した詳細情報を
    Slack表示用テキストに変換する。

    取得できない情報は表示しない。

    license はAPIから返された値を
    そのまま表示する。
    """

    lines = []

    # --------------------------------------
    # Author
    # --------------------------------------

    author = item.get(
        "author"
    )

    if isinstance(
        author,
        str,
    ) and author.strip():

        lines.append(
            f"  作者：{author.strip()}"
        )

    # --------------------------------------
    # Tags
    # --------------------------------------

    source_tags = item.get(
        "source_tags"
    )

    if isinstance(
        source_tags,
        list,
    ):

        clean_tags = []

        for tag in source_tags:

            if not isinstance(
                tag,
                str,
            ):
                continue

            tag = tag.strip()

            if not tag:
                continue

            if tag not in clean_tags:
                clean_tags.append(
                    tag
                )

        if clean_tags:

            # Slackが長くなりすぎないように
            # 最大20タグまで表示。
            display_tags = clean_tags[:20]

            tag_text = ", ".join(
                display_tags
            )

            if len(clean_tags) > 20:
                tag_text += " ..."

            lines.append(
                f"  タグ：{tag_text}"
            )

    # --------------------------------------
    # License
    # --------------------------------------

    license_name = item.get(
        "license"
    )

    if isinstance(
        license_name,
        str,
    ) and license_name.strip():

        lines.append(
            "  ライセンス："
            f"{license_name.strip()}"
        )

    # --------------------------------------
    # Download
    # --------------------------------------

    is_downloadable = item.get(
        "is_downloadable"
    )

    if isinstance(
        is_downloadable,
        bool,
    ):

        if is_downloadable:

            lines.append(
                "  ダウンロード：可能"
            )

        else:

            lines.append(
                "  ダウンロード：不可"
            )

    # --------------------------------------
    # Mature
    # --------------------------------------

    is_mature = item.get(
        "is_mature"
    )

    if is_mature is True:

        lines.append(
            "  Mature：あり"
        )

    # --------------------------------------
    # Description
    # --------------------------------------

    description = item.get(
        "description"
    )

    if isinstance(
        description,
        str,
    ):

        description = description.strip()

        if description:

            # 改行をSlack上で扱いやすくする。
            description = (
                description
                .replace("\r\n", " ")
                .replace("\n", " ")
                .replace("\r", " ")
            )

            # 連続空白を整理。
            while "  " in description:
                description = (
                    description.replace(
                        "  ",
                        " ",
                    )
                )

            # 長すぎる説明は切る。
            max_length = 300

            if len(description) > max_length:

                description = (
                    description[
                        :max_length
                    ].rstrip()
                    + "..."
                )

            lines.append(
                f"  説明：{description}"
            )

    # --------------------------------------
    # Content size
    # --------------------------------------

    width = item.get(
        "content_width"
    )

    height = item.get(
        "content_height"
    )

    if (
        width is not None
        and height is not None
    ):

        lines.append(
            f"  サイズ：{width} × {height}"
        )

    return lines


# ==========================================
# Report
# ==========================================

def build_report(items):

    now = now_jst()

    date_str = now.strftime(
        "%Y.%m.%d"
    )

    period = get_period()

    if not items:

        return (
            f"📬 RPG Maker Daily Report\n"
            f"{date_str} {period}\n"
            "\n"
            "新着ニュースはありません。\n"
            "\n"
            "────────────────────\n"
            "【SOURCE CHECK】\n"
            "・<https://www.gamedevmarket.net/|GameDevMarket>"
            " ▶ 素材のセルフチェック"
        )

    categories = {}

    # --------------------------------------
    # カテゴリ整理
    # --------------------------------------

    for item in items:

        item = item.copy()

        category = item.get(
            "category",
            "",
        )

        display_category = get_display_category(
            category
        )

        item["display_category"] = (
            display_category
        )

        categories.setdefault(
            display_category,
            [],
        ).append(item)

    report = []

    report.append(
        "📬 RPG Maker Daily Report"
    )

    report.append(
        f"{date_str} {period}"
    )

    report.append("")

    # --------------------------------------
    # Summary
    # --------------------------------------

    summary_groups = {
        "今日の注目": [],
        "新作ゲーム": [],
        "プラグイン・素材": [],
        "開発情報・Tips": [],
        "質問・相談": [],
    }

    for category, category_items in categories.items():

        group = get_report_group(
            category
        )

        if group:

            summary_groups[group].extend(
                category_items
            )

    summary_headers = {
        "今日の注目": "★★★★★ 今日の注目",
        "新作ゲーム": "★★★★☆ 新作ゲーム",
        "プラグイン・素材": "★★★☆☆ プラグイン・素材",
        "開発情報・Tips": "★★☆☆☆ 開発情報・Tips",
        "質問・相談": "★☆☆☆☆ 質問・相談",
    }

    for group, group_items in summary_groups.items():

        if not group_items:
            continue

        report.append(
            f"{summary_headers[group]}"
            f"（{len(group_items)}件）"
        )

    report.append("")

    report.append(
        "────────────────────"
    )

    report.append("")

    # --------------------------------------
    # Detail
    # --------------------------------------

    detail_order = [
        "本体ニュース",
        "UNITE",
        "Forum重要事項",
        "プラグイン",
        "グラフィック素材",
        "サウンド素材",
        "ゲーム",
        "Tips",
        "質問",
    ]

    for category in detail_order:

        if category not in categories:
            continue

        report.append(
            f"【{category}】"
        )

        grouped = {}

        for item in categories[category]:

            title = item.get(
                "title",
                "タイトルなし",
            )

            url = item.get(
                "url",
                "",
            )

            source = item.get(
                "source",
                "",
            )

            key = title.lower().strip()

            # ----------------------------------
            # 同一タイトルをまとめる
            # ----------------------------------

            if key not in grouped:

                grouped[key] = {
                    "title": title,
                    "url": url,
                    "sources": [],
                    "items": [],
                }

            if source:

                grouped[key][
                    "sources"
                ].append(
                    source
                )

            grouped[key][
                "items"
            ].append(
                item
            )

        for entry in grouped.values():

            source_text = " / ".join(
                sorted(
                    set(
                        entry["sources"]
                    )
                )
            )

            title = entry["title"]
            url = entry["url"]

            # ----------------------------------
            # Slack link
            # ----------------------------------

            link = (
                f"<{url}|{title}>"
                if url
                else title
            )

            if source_text:

                report.append(
                    f"・[{source_text}] {link}"
                )

            else:

                report.append(
                    f"・{link}"
                )

            # ----------------------------------
            # DeviantArt詳細
            #
            # 同一タイトルが複数ソースから
            # 来た場合も、DeviantArtだけを表示。
            # ----------------------------------

            for item in entry["items"]:

                if item.get(
                    "source"
                ) != "DeviantArt":
                    continue

                detail_lines = (
                    format_deviantart_detail(
                        item
                    )
                )

                for detail_line in (
                    detail_lines
                ):

                    report.append(
                        detail_line
                    )

        report.append("")

    # --------------------------------------
    # Source Check
    # --------------------------------------

    report.append(
        "────────────────────"
    )

    report.append(
        "【SOURCE CHECK】"
    )

    report.append(
        "・<https://www.gamedevmarket.net/|GameDevMarket>"
        " ▶ 素材のセルフチェック"
    )

    return "\n".join(report)


# ==========================================
# Slack
# ==========================================

def send_to_slack(message):

    webhook_url = os.getenv(
        SLACK_WEBHOOK_ENV
    )

    if not webhook_url:

        print(
            "SLACK_WEBHOOK_URL がありません"
        )

        return

    response = requests.post(
        webhook_url,
        json={
            "text": message
        },
        timeout=REQUEST_TIMEOUT,
    )

    print(
        "Slack status:",
        response.status_code,
    )
