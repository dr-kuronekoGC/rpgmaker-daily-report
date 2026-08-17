# ==========================================
# DeviantArt
# ==========================================

import os

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
# API request
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

    if not isinstance(results, list):
        return []

    # ==================================
    # DEBUG: DeviantArt API response
    # ==================================

    if results:
        print(
            "[DeviantArt][DEBUG] "
            "First result:"
        )
        print(results[0])

    return results

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
        # 複数タグを検索
        # ----------------------------------

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

                # --------------------------------
                # APIから取得する基本情報
                # --------------------------------

                href = result.get(
                    "url"
                )

                title = result.get(
                    "title"
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

                # --------------------------------
                # 同一実行内の重複
                # --------------------------------

                if href in seen_urls:
                    continue

                seen_urls.add(href)

                # --------------------------------
                # 過去取得
                # --------------------------------

                if href in seen:
                    continue

                # --------------------------------
                # 素材分類
                # --------------------------------

                result_classification = (
                    classify_asset(
                        title,
                        href,
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

                # --------------------------------
                # 素材でなければ除外
                # --------------------------------

                if category is None:
                    continue

                # --------------------------------
                # 採用
                # --------------------------------

                item = {
                    "title": title,
                    "url": href,
                    "category": category,
                    "source": "DeviantArt",
                }

                if tags:
                    item["tags"] = tags

                # --------------------------------
                # 作者情報
                # --------------------------------

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
            f"[DeviantArt] HTTP Error: {e}"
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
            f"[DeviantArt] Error: {e}"
        )

        return [], seen
