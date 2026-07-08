
import json

from pathlib import Path
from datetime import datetime, timedelta


# ----------------------------
# 日本時間
# ----------------------------

def now_jst():
    return datetime.utcnow() + timedelta(hours=9)

def get_period():
    hour = now_jst().hour
    if 5 <= hour < 10:
        return "朝"
    elif 10 <= hour < 15:
        return "昼"
    elif 15 <= hour < 18:
        return "夕"
    else:
        return "夜"

# ----------------------------
# seen ファイル
# ----------------------------

def load_seen_file(filename):

    path = Path(filename)

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_seen_file(filename, data):

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )


# ----------------------------
# 互換関数
# ----------------------------

def load_seen():

    return load_seen_file(
        "seen.json"
    )


def save_seen(data):

    save_seen_file(
        "seen.json",
        data
    )
