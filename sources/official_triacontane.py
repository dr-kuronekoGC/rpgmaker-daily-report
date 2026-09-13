# ==========================================
# triacontane
# ==========================================

import os
import re
import requests

from config import (
    TRIACONTANE_REPO_URL,
    TRIACONTANE_BRANCH,
    TRIACONTANE_SEEN_FILE,
    REQUEST_TIMEOUT,
    USER_AGENT,
)

SEEN_FILE = TRIACONTANE_SEEN_FILE

HEADERS = {
    "User-Agent": USER_AGENT,
    "Authorization": (
        f"Bearer {os.environ.get('GITHUB_TOKEN', '')}"
    ),
    "Accept": "application/vnd.github+json",
}

API_URL = (
    "https://api.github.com/repos/"
    "triacontane/RPGMakerMV/contents"
)

PLUGIN_EXTENSIONS = (
    ".js",
)

IGNORE_FILES = {
    "PluginCommonBase.js",
}


def get_json(url):
    response = requests.get(
        url,
        headers=HEADERS,
        params={
            "ref": TRIACONTANE_BRANCH,
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def is_plugin_file(name):
    if not name:
        return False

    if name in IGNORE_FILES:
        return False

    if not name.lower().endswith(PLUGIN_EXTENSIONS):
        return False

    return True


def clean_title(name):
    if not name:
        return None

    title = name.strip()

    if title.lower().endswith(".js"):
        title = title[:-3]

    title = re.sub(
        r"^triacontane[_\-]",
        "",
        title,
        flags=re.IGNORECASE,
    )

    if not title:
        return None

    return title


def get_root_files():
    data = get_json(API_URL)

    if not isinstance(data, list):
        return []

    return data


def build_current_state(files):
    """
    現在のプラグイン状態を
    path -> GitHub blob SHA
    の辞書として作る。
    """

    current_state = {}

    for entry in files:
        if not isinstance(entry, dict):
            continue

        if entry.get("type") != "file":
            continue

        name = entry.get("name")
        if not is_plugin_file(name):
            continue

        path = entry.get("path")
        sha = entry.get("sha")

        if not path or not sha:
            continue

        if path != name:
            continue

        current_state[path] = sha

    return current_state


def get_items(seen):
    """
    triacontaneのルート直下にあるMZプラグインを監視する。

    seenは
        {"path": "sha"}
    の辞書を基本形式とする。

    初回実行時、または旧形式（pathのリスト）からの移行時は、
    現在存在するプラグインをベースラインとして記録するだけで、
    Slack掲載用のItemは生成しない。

    2回目以降は、
    - 新しく追加されたファイル
    - GitHub上でSHAが変わったファイル
    を新規Itemとして返す。
    """

    adopted_items = []

    try:
        files = get_root_files()
        current_state = build_current_state(files)

        # --------------------------------------
        # 初回・旧形式からの移行
        # --------------------------------------
        #
        # 以前は「pathのリスト」だったため、
        # SHA情報がない状態では更新判定ができない。
        # この場合は現在状態をベースラインとして保存し、
        # 過去の555件などを再度掲載しない。
        #
        if not isinstance(seen, dict):
            print(
                "[triacontane] Baseline: "
                f"{len(current_state)} plugins"
            )
            return adopted_items, current_state

        new_state = dict(seen)

        # --------------------------------------
        # 新規追加・更新を検出
        # --------------------------------------

        for path, sha in current_state.items():
            previous_sha = seen.get(path)

            # 新規ファイル
            if previous_sha is None:
                changed_type = "New"

            # 既存ファイルの更新
            elif previous_sha != sha:
                changed_type = "Updated"

            else:
                continue

            name = path
            title = clean_title(name)

            if not title:
                continue

            html_url = (
                "https://github.com/triacontane/"
                f"RPGMakerMV/blob/{TRIACONTANE_BRANCH}/{path}"
            )

            adopted_items.append(
                {
                    "title": title,
                    "url": html_url,
                    "category": "プラグイン",
                    "source": "triacontane",
                }
            )

            print(
                "[triacontane]"
                f"[プラグイン] {changed_type}: {title}"
            )

            new_state[path] = sha

        # --------------------------------------
        # 削除されたファイルは掲載しない
        # --------------------------------------
        #
        # 削除は情報収集対象ではなく、
        # 現在状態から自然に消えるだけとする。
        #
        new_state = {
            path: sha
            for path, sha in new_state.items()
            if path in current_state
        }

        print(
            "[triacontane] New/Updated: "
            f"{len(adopted_items)}"
        )

        return adopted_items, new_state

    except Exception as e:
        print(
            f"[triacontane] Error: {e}"
        )

        # エラー時はseenを変更しない。
        return [], seen
