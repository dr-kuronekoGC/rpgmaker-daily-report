import json
from pathlib import Path
from datetime import UTC, datetime, timedelta

# ==========================================
# Date / Time
# ==========================================

def now_jst() -> datetime:
    """
    日本時間(datetime)を返す
    """
    return datetime.now(UTC) + timedelta(hours=9)


def get_period() -> str:
    """
    現在時刻から時間帯を返す
    """

    hour = now_jst().hour

    if 5 <= hour < 10:
        return "朝"

    if 10 <= hour < 15:
        return "昼"

    if 15 <= hour < 18:
        return "夕"

    return "夜"


# ==========================================
# seen file
# ==========================================

def load_seen_file(filename: str) -> list:
    """
    seenファイルを読み込む
    """

    path = Path(filename)

    if not path.exists():
        return []

    with path.open(
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def save_seen_file(
    filename: str,
    data: list,
) -> None:
    """
    seenファイルを保存する
    """

    path = Path(filename)

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

# ==========================================
# pending items
# ==========================================

def load_pending_items(filename: str) -> list:
    """
    掲載待ちItemを読み込む
    """

    path = Path(filename)

    if not path.exists():
        return []

    with path.open(
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def save_pending_items(
    filename: str,
    data: list,
) -> None:
    """
    掲載待ちItemを保存する
    """

    path = Path(filename)

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
