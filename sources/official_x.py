import os
import requests

from config import (
    OFFICIAL_X_ACCOUNTS,
    OFFICIAL_X_SEEN_FILE,
    REQUEST_TIMEOUT,
)

from categories import classify_official


SEEN_FILE = OFFICIAL_X_SEEN_FILE

X_API_BASE_URL = "https://api.x.com/2"


def get_bearer_token():
    """
    GitHub Actions Secretsから
    X APIのBearer Tokenを取得する。
    """

    token = os.getenv(
        "X_BEARER_TOKEN"
    )

    if not token:
        raise RuntimeError(
            "X_BEARER_TOKEN が設定されていません。"
        )

    return token


def get_user_id(
    username,
    headers,
):
    """
    Xユーザー名からUser IDを取得する。
    """

    url = (
        f"{X_API_BASE_URL}"
        f"/users/by/username/{username}"
    )

    response = requests.get(
        url,
        headers=headers,
        params={
            "user.fields": "username,name",
        },
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    user = data.get(
        "data"
    )

    if not user:
        raise RuntimeError(
            f"Xユーザーが見つかりません: @{username}"
        )

    return user["id"]


def get_user_posts(
    user_id,
    headers,
):
    """
    Xユーザーの最新投稿を取得する。

    返信・リポストは除外する。
    """

    url = (
        f"{X_API_BASE_URL}"
        f"/users/{user_id}/tweets"
    )

    response = requests.get(
        url,
        headers=headers,
        params={
            "max_results": 10,
            "exclude": "replies,retweets",
            "tweet.fields": "created_at",
        },
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    return data.get(
        "data",
        [],
    )


def build_title(
    text,
):
    """
    投稿本文からSlack表示用の短いタイトルを作る。

    本文そのものをdescriptionとして保存するのではなく、
    「リンク先が何なのか分かる程度」のタイトルだけ作る。
    """

    if not isinstance(
        text,
        str,
    ):
        return "公式Xの新着投稿"

    text = text.strip()

    if not text:
        return "公式Xの新着投稿"

    # 改行を整理
    text = (
        text
        .replace("\r\n", " ")
        .replace("\n", " ")
        .replace("\r", " ")
    )

    while "  " in text:
        text = text.replace(
            "  ",
            " ",
        )

    # Slackが長くなりすぎないようにする
    max_length = 80

    if len(text) > max_length:
        return (
            text[:max_length].rstrip()
            + "..."
        )

    return text


def get_items(
    seen,
):
    """
    公式Xの新着投稿を取得する。

    投稿本文を保存することが目的ではなく、
    新しい投稿があったことと、
    その投稿へのリンクを取得することが目的。
    """

    adopted_items = []

    new_seen = seen.copy()

    try:

        bearer_token = get_bearer_token()

        headers = {
            "Authorization": (
                f"Bearer {bearer_token}"
            )
        }

        for account in OFFICIAL_X_ACCOUNTS:

            username = account.get(
                "username"
            )

            display_name = account.get(
                "name",
                f"@{username}",
            )

            if not username:
                continue

            print(
                "[Official X] Checking "
                f"@{username}"
            )

            user_id = get_user_id(
                username,
                headers,
            )

            posts = get_user_posts(
                user_id,
                headers,
            )

            for post in posts:

                post_id = post.get(
                    "id"
                )

                if not post_id:
                    continue

                if post_id in seen:
                    continue

                new_seen.append(
                    post_id
                )

                text = post.get(
                    "text",
                    "",
                )

                url = (
                    f"https://x.com/"
                    f"{username}/status/"
                    f"{post_id}"
                )

                title = build_title(
                    text
                )

                category = classify_official(
                    title,
                    url,
                )

                # Xでは分類できない投稿も
                # 「公式X」として拾う。
                if category is None:
                    category = "本体ニュース"

                item = {
                    "title": title,
                    "url": url,
                    "category": category,
                    "source": display_name,
                }

                adopted_items.append(
                    item
                )

                print(
                    "[Official X]"
                    f" [{display_name}] "
                    f"{title}"
                )

        print(
            "[Official X] New: "
            f"{len(adopted_items)}"
        )

    except Exception as e:

        print(
            "[Official X] Error:",
            e,
        )

    return (
        adopted_items,
        new_seen,
    )
