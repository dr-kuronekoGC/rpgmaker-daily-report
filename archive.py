import json
from pathlib import Path

from common import now_jst


ARCHIVE_DIR = Path("data/archive")
ARCHIVE_INDEX_FILE = ARCHIVE_DIR / "archive_index.json"


def get_archive_file():
    """
    現在年月のArchiveファイルを返す。
    """

    now = now_jst()

    filename = (
        f"{now.year:04d}-"
        f"{now.month:02d}.json"
    )

    return ARCHIVE_DIR / filename


def load_json_list(path):
    """
    JSON配列を読み込む。

    ファイルが存在しない、または壊れている場合は
    空のリストを返す。
    """

    if not path.exists():
        return []

    with path.open(
        "r",
        encoding="utf-8",
    ) as f:

        try:
            data = json.load(f)

        except json.JSONDecodeError:
            return []

    if not isinstance(data, list):
        return []

    return data


def save_json_list(path, data):
    """
    JSON配列を保存する。
    """

    with path.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
        )


def get_archive_key(item):
    """
    Archive内の重複判定用キー。

    URLを基本キーとする。
    """

    url = item.get("url")

    if isinstance(url, str):

        url = url.strip()

        if url:
            return url

    return None


def load_archive_index():
    """
    Archive全体のURLインデックスを読み込む。
    """

    return set(
        load_json_list(
            ARCHIVE_INDEX_FILE
        )
    )


def save_archive_index(index):
    """
    Archive全体のURLインデックスを保存する。
    """

    save_json_list(
        ARCHIVE_INDEX_FILE,
        sorted(index),
    )


def save_archive(items):
    """
    新規Itemを月別Archiveへ保存する。

    同じURLは月をまたいでも重複保存しない。
    """

    if not items:
        return

    ARCHIVE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = get_archive_file()

    archive = load_json_list(path)

    archive_index = load_archive_index()

    added = 0

    for item in items:

        key = get_archive_key(item)

        if key is not None:

            if key in archive_index:
                continue

        archived_item = dict(item)

        if "collected_at" not in archived_item:
            archived_item["collected_at"] = (
                now_jst().isoformat()
            )

        archive.append(
            archived_item
        )

        if key is not None:
            archive_index.add(key)

        added += 1

    if added == 0:
        print(
            "[Archive] Added: 0"
        )
        return

    save_json_list(
        path,
        archive,
    )

    save_archive_index(
        archive_index
    )

    print(
        "[Archive] Added:",
        added,
    )

    print(
        "[Archive] Total:",
        len(archive),
    )

    print(
        "[Archive] Index:",
        len(archive_index),
    )