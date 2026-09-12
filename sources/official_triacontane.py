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
    url = API_URL

    data = get_json(url)

    if not isinstance(data, list):
        return []

    return data


def get_items(seen):
    adopted_items = []
    new_seen = seen.copy()

    try:
        files = get_root_files()

        for entry in files:
            if not isinstance(entry, dict):
                continue

            if entry.get("type") != "file":
                continue

            name = entry.get("name")

            if not is_plugin_file(name):
                continue

            path = entry.get("path")
            html_url = entry.get("html_url")

            if not path or not html_url:
                continue

            if path != name:
                continue

            if path in seen:
                continue

            title = clean_title(name)

            if not title:
                continue

            new_seen.append(path)

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
                f"[プラグイン] {title}"
            )

        print(
            "[triacontane] New: "
            f"{len(adopted_items)}"
        )

        return adopted_items, new_seen

    except Exception as e:
        print(
            f"[triacontane] Error: {e}"
        )

        return [], seen
