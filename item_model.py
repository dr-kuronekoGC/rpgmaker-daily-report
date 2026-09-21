import hashlib
from datetime import datetime, timezone
from pathlib import Path
import json

from common import now_jst
from asset_metadata import enrich_items


SITES_FILE = Path("data/sites/sites.json")


def _load_sites():
    if not SITES_FILE.exists():
        return {}
    try:
        with SITES_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, list):
        return {}
    return {
        item.get("collector"): item.get("source_site_id")
        for item in data
        if isinstance(item, dict)
        and item.get("collector")
        and item.get("source_site_id")
    }


def _stable_id(source_site_id, source_item_id, url):
    raw = f"{source_site_id}|{source_item_id or url}".encode("utf-8")
    return "ITEM-" + hashlib.sha256(raw).hexdigest()[:16]


def _content_type(item):
    category = str(item.get("category", "")).lower()
    asset_type = item.get("asset_type")

    if asset_type == "plugin" or "plugin" in category or "プラグイン" in category:
        return "plugin"
    if asset_type == "game" or category in {"ゲーム", "game"}:
        return "game"
    if item.get("source_site_type") == "official" or category in {"公式情報", "公式", "SourceCheck"}:
        return "official"
    if category == "サイト更新":
        return "site_update"
    if asset_type in {"graphic", "sound"}:
        return "asset"
    if any(x in category for x in ("素材", "グラフィック", "サウンド")):
        return "asset"
    return "other"


def _normalize_list(value):
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def normalize_item(item, collector_name):
    item = dict(item)
    sites = _load_sites()

    source_site_id = item.get("source_site_id") or sites.get(collector_name) or "SITE-UNREGISTERED"
    url = str(item.get("url", "")).strip()
    source_item_id = item.get("source_item_id") or url
    internal_id = item.get("internal_id") or _stable_id(
        source_site_id, str(source_item_id), url
    )

    current_language = item.get("language")
    languages = _normalize_list(item.get("languages"))
    if not languages and current_language:
        languages = [current_language]

    tags = _normalize_list(item.get("tags"))
    if not tags:
        tags = _normalize_list(item.get("source_tags"))

    subcategory = _normalize_list(item.get("subcategory"))
    plugin_category = _normalize_list(item.get("plugin_category"))

    now = now_jst().isoformat()

    item["internal_id"] = internal_id
    item.setdefault("pre_id", None)
    item.setdefault("public_id", None)
    item["content_type"] = item.get("content_type") or _content_type(item)
    item["source_site_id"] = source_site_id
    item["collector"] = collector_name
    item["source_item_id"] = str(source_item_id)
    item["subcategory"] = subcategory
    item["tags"] = tags
    item["languages"] = languages
    item.setdefault("sound_type", None)
    item["plugin_category"] = plugin_category
    item.setdefault("commercial_use", None)
    item.setdefault("credit_required", None)
    item.setdefault("redistribution_allowed", None)
    item.setdefault("source_published_at", item.get("published_at"))
    item.setdefault("source_updated_at", item.get("updated_at"))
    item.setdefault("first_seen_at", now)
    # registered_at is intentionally NOT set here.
    item.setdefault("registered_at", None)
    item.setdefault("thumbnail_url", None)
    item.setdefault("editorial_status", "new")
    item.setdefault("excluded_reason", None)
    item.setdefault("review_note", None)
    item.setdefault("reviewed_at", None)
    item.setdefault("featured", False)

    return item


def normalize_items(items, collector_name):
    return [normalize_item(item, collector_name) for item in items]


def collect_and_enrich(items, collector_name):
    normalized = normalize_items(items, collector_name)
    return enrich_items(normalized)
