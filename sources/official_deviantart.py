# ==========================================
# DeviantArt
# ==========================================

import html
import os
import re

import requests

from config import (
    DEVIANTART_SEARCHES,
    DEVIANTART_SEEN_FILE,
)

from categories.assets import (
    classify_asset,
)


SEEN_FILE = DEVIANTART_SEEN_FILE


DEVIANTART_API_BASE_URL = (
    "https://www.deviantart.com/api/v1/oauth2"
)

DEVIANTART_TOKEN_URL = (
    "https://www.deviantart.com/oauth2/token"
)

DEVIANTART_TAG_URL = (
    DEVIANTART_API_BASE_URL
    + "/browse/tags"
)

DEVIANTART_METADATA_URL = (
    DEVIANTART_API_BASE_URL
    + "/deviation/metadata"
)


# ==========================================
# OAuth2
# ==========================================

def get_access_token():

    client_id = os.getenv(
        "DEVIANTART_CLIENT_ID"
    )

    client_secret = os.getenv(
        "DEVIANTART_CLIENT_SECRET"
    )

    if not client_id or not client_secret:
        raise RuntimeError(
            "DEVIANTART_CLIENT_ID / "
            "DEVIANTART_CLIENT_SECRET "
            "are not configured"
        )

    response = requests.post(
        DEVIANTART_TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={
            "User-Agent": (
                "RPG Maker Daily Report/1.0"
            ),
            "Accept-Encoding": (
                "gzip, deflate"
            ),
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    access_token = data.get(
        "access_token"
    )

    if not access_token:
        raise RuntimeError(
            "DeviantArt token response did not "
            "contain access_token"
        )

    return access_token


# ==========================================
# Tag Search
# ==========================================

def browse_tag(
    access_token,
    tag,
    limit=50,
):

    response = requests.get(
        DEVIANTART_TAG_URL,
        params={
            "tag": tag,
            "offset": 0,
            "limit": limit,
            "with_session": "false",
        },
        headers={
            "Accept": "application/json",
            "Authorization": (
                f"Bearer {access_token}"
            ),
            "User-Agent": (
                "RPG Maker Daily Report/1.0"
            ),
            "Accept-Encoding": (
                "gzip, deflate"
            ),
            "dA-minor-version": "20240701",
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    results = data.get(
        "results",
        [],
    )

    if not isinstance(
        results,
        list,
    ):
        return []

    return results


# ==========================================
# Metadata API
# ==========================================

def get_deviation_metadata(
    access_token,
    deviation_ids,
):
    """
    複数DeviationのMetadataを取得する。

    DeviantArt APIの仕様上、
    1回のリクエストは最大50件を想定。
    """

    if not deviation_ids:
        return {}

    params = []

    for index, deviation_id in enumerate(
        deviation_ids
    ):
        params.append(
            (
                f"deviationids[{index}]",
                deviation_id,
            )
        )

    response = requests.get(
        DEVIANTART_METADATA_URL,
        params=params,
        headers={
            "Accept": "application/json",
            "Authorization": (
                f"Bearer {access_token}"
            ),
            "User-Agent": (
                "RPG Maker Daily Report/1.0"
            ),
            "Accept-Encoding": (
                "gzip, deflate"
            ),
            "dA-minor-version": "20240701",
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(
        data,
        dict,
    ):
        return {}

    metadata_list = data.get(
        "metadata",
        [],
    )

    if not isinstance(
        metadata_list,
        list,
    ):
        return {}

    metadata_by_id = {}

    for metadata in metadata_list:

        if not isinstance(
            metadata,
            dict,
        ):
            continue

        deviation_id = metadata.get(
            "deviationid"
        )

        if deviation_id:
            metadata_by_id[
                deviation_id
            ] = metadata

    return metadata_by_id


# ==========================================
# HTML description cleanup
# ==========================================

def clean_description(
    value,
):
    """
    DeviantArtのHTML説明文を
    Slack表示用のプレーンテキストにする。

    URLなどの情報を無理に解析せず、
    まずは本文だけを安全に取り出す。
    """

    if not isinstance(
        value,
        str,
    ):
        return ""

    text = value

    # 改行相当
    text = re.sub(
        r"<br\s*/?>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"</p\s*>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"</div\s*>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    # HTMLタグ除去
    text = re.sub(
        r"<[^>]+>",
        "",
        text,
    )

    # HTML entity
    text = html.unescape(
        text
    )

    # 空白整理
    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n\s*\n+",
        "\n\n",
        text,
    )

    return text.strip()


# ==========================================
# Metadata tags
# ==========================================

def extract_metadata_tags(
    metadata,
):
    """
    Metadata APIのtagsから
    タグ名だけを取り出す。
    """

    tags = []

    raw_tags = metadata.get(
        "tags",
        [],
    )

    if not isinstance(
        raw_tags,
        list,
    ):
        return tags

    for tag in raw_tags:

        if not isinstance(
            tag,
            dict,
        ):
            continue

        tag_name = tag.get(
            "tag_name"
        )

        if not isinstance(
            tag_name,
            str,
        ):
            continue

        tag_name = (
            tag_name
            .strip()
            .lower()
        )

        if (
            tag_name
            and tag_name not in tags
        ):
            tags.append(
                tag_name
            )

    return tags


# ==========================================
# Main
# ==========================================

def get_items(seen):

    try:

        adopted_items = []

        new_seen = seen.copy()

        seen_urls = set()

        # ----------------------------------
        # OAuth2
        # ----------------------------------

        access_token = get_access_token()

        # ----------------------------------
        # Search results
        # ----------------------------------

        search_items = []

        for tag in DEVIANTART_SEARCHES:

            normalized_tag = (
                tag.strip()
                .lower()
                .replace(" ", "")
            )

            if not normalized_tag:
                continue

            print(
                f"[DeviantArt] Tag search: "
                f"{normalized_tag}"
            )

            results = browse_tag(
                access_token,
                normalized_tag,
            )

            print(
                f"[DeviantArt] Results: "
                f"{len(results)}"
            )

            for result in results:

                if not isinstance(
                    result,
                    dict,
                ):
                    continue

                href = result.get(
                    "url"
                )

                title = result.get(
                    "title"
                )

                deviation_id = result.get(
                    "deviationid"
                )

                if not href or not title:
                    continue

                if not isinstance(
                    href,
                    str,
                ):
                    continue

                if not isinstance(
                    title,
                    str,
                ):
                    continue

                if (
                    href in seen_urls
                ):
                    continue

                seen_urls.add(
                    href
                )

                # ----------------------------------
                # 既読
                # ----------------------------------

                if href in seen:
                    continue

                search_items.append(
                    result
                )

        # ----------------------------------
        # Metadata取得対象
        # ----------------------------------

        unique_items = []

        seen_deviation_ids = set()

        for result in search_items:

            deviation_id = result.get(
                "deviationid"
            )

            if not deviation_id:
                continue

            if (
                deviation_id
                in seen_deviation_ids
            ):
                continue

            seen_deviation_ids.add(
                deviation_id
            )

            unique_items.append(
                result
            )

        # ----------------------------------
        # Metadata API
        #
        # 最大50件ずつ取得
        # ----------------------------------

        metadata_by_id = {}

        for start in range(
            0,
            len(unique_items),
            50,
        ):

            batch = unique_items[
                start:start + 50
            ]

            batch_ids = [
                item.get(
                    "deviationid"
                )
                for item in batch
                if item.get(
                    "deviationid"
                )
            ]

            try:

                batch_metadata = (
                    get_deviation_metadata(
                        access_token,
                        batch_ids,
                    )
                )

                metadata_by_id.update(
                    batch_metadata
                )

                print(
                    "[DeviantArt] Metadata: "
                    f"{len(batch_metadata)} "
                    "items"
                )

            except requests.HTTPError as e:

                print(
                    "[DeviantArt] Metadata "
                    "HTTP Error: "
                    f"{e}"
                )

                if getattr(
                    e,
                    "response",
                    None,
                ) is not None:

                    print(
                        "[DeviantArt] Metadata "
                        "Response: "
                        f"{e.response.text[:500]}"
                    )

            except Exception as e:

                print(
                    "[DeviantArt] Metadata "
                    "Error: "
                    f"{e}"
                )

        # ----------------------------------
        # 各作品を処理
        # ----------------------------------

        for result in unique_items:

            href = result.get(
                "url"
            )

            title = result.get(
                "title"
            )

            deviation_id = result.get(
                "deviationid"
            )

            if not href or not title:
                continue

            metadata = metadata_by_id.get(
                deviation_id,
                {},
            )

            # ----------------------------------
            # Metadata情報
            # ----------------------------------

            metadata_title = metadata.get(
                "title"
            )

            if isinstance(
                metadata_title,
                str,
            ) and metadata_title.strip():

                title = (
                    metadata_title.strip()
                )

            source_tags = (
                extract_metadata_tags(
                    metadata
                )
            )

            description = clean_description(
                metadata.get(
                    "description"
                )
            )

            license_name = metadata.get(
                "license"
            )

            if not isinstance(
                license_name,
                str,
            ):
                license_name = None

            # ----------------------------------
            # 素材分類
            #
            # タイトルだけでなく
            # DeviantArtタグも使用する。
            # ----------------------------------

            result_classification = (
                classify_asset(
                    title,
                    href,
                    source_tags=source_tags,
                    is_downloadable=result.get(
                        "is_downloadable"
                    ),
                    description=description,
                )
            )

            if isinstance(
                result_classification,
                tuple,
            ):

                category = (
                    result_classification[0]
                )

                tags = (
                    result_classification[1]
                )

            else:

                category = (
                    result_classification
                )

                tags = []

            # ----------------------------------
            # 素材でなければ除外
            # ----------------------------------

            if category is None:
                continue

            # ----------------------------------
            # 基本item
            # ----------------------------------

            item = {
                "title": title,
                "url": href,
                "category": category,
                "source": "DeviantArt",
            }

            if tags:
                item["tags"] = tags

            # ----------------------------------
            # 作者
            # ----------------------------------

            author = metadata.get(
                "author"
            )

            if not isinstance(
                author,
                dict,
            ):
                author = result.get(
                    "author"
                )

            if isinstance(
                author,
                dict,
            ):

                username = author.get(
                    "username"
                )

                if username:
                    item["author"] = (
                        username
                    )

            # ----------------------------------
            # Deviation ID
            # ----------------------------------

            if deviation_id:
                item["deviationid"] = (
                    deviation_id
                )

            # ----------------------------------
            # Published time
            # ----------------------------------

            published_time = result.get(
                "published_time"
            )

            if published_time:
                item["published_time"] = (
                    published_time
                )

            # ----------------------------------
            # Download information
            # ----------------------------------

            is_downloadable = result.get(
                "is_downloadable"
            )

            if isinstance(
                is_downloadable,
                bool,
            ):
                item[
                    "is_downloadable"
                ] = is_downloadable

            download_filesize = result.get(
                "download_filesize"
            )

            if download_filesize is not None:
                item[
                    "download_filesize"
                ] = download_filesize

            # ----------------------------------
            # Content information
            # ----------------------------------

            content = result.get(
                "content"
            )

            if isinstance(
                content,
                dict,
            ):

                for key in (
                    "width",
                    "height",
                    "filesize",
                    "transparency",
                ):

                    value = content.get(
                        key
                    )

                    if value is not None:
                        item[
                            f"content_{key}"
                        ] = value

            # ----------------------------------
            # Mature
            # ----------------------------------

            is_mature = result.get(
                "is_mature"
            )

            if isinstance(
                is_mature,
                bool,
            ):
                item[
                    "is_mature"
                ] = is_mature

            # ----------------------------------
            # DeviantArt metadata
            # ----------------------------------

            if source_tags:
                item[
                    "source_tags"
                ] = source_tags

            if description:
                item[
                    "description"
                ] = description

            if license_name:
                item[
                    "license"
                ] = license_name

            # ----------------------------------
            # Adopt
            # ----------------------------------

            adopted_items.append(
                item
            )

            new_seen.append(
                href
            )

            print(
                f"[DeviantArt]"
                f"[{category}] "
                f"{title}"
            )

        print(
            f"[DeviantArt] New: "
            f"{len(adopted_items)}"
        )

        return (
            adopted_items,
            new_seen,
        )

    except requests.HTTPError as e:

        print(
            f"[DeviantArt] HTTP Error: "
            f"{e}"
        )

        if getattr(
            e,
            "response",
            None,
        ) is not None:

            print(
                "[DeviantArt] Response: "
                f"{e.response.text[:500]}"
            )

        return [], seen

    except Exception as e:

        print(
            f"[DeviantArt] Error: "
            f"{e}"
        )

        return [], seen
