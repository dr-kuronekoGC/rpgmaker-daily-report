import hashlib
from pathlib import Path
from datetime import datetime, timezone

import json

from common import now_jst
from asset_metadata import enrich_items


SITES_FILE = Path("data/sites/sites.json")


def _load_sites():
    """Return site metadata keyed by collector, preserving the registry as source of truth."""
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
        record.get("collector"): record
        for record in data
        if isinstance(record, dict)
        and record.get("collector")
        and record.get("source_site_id")
    }


def _stable_id(source_site_id, source_item_id, url):
    raw = f"{source_site_id}|{source_item_id or url}".encode("utf-8")
    return "ITEM-" + hashlib.sha256(raw).hexdigest()[:16]


def _is_tips_category(category):
    normalized = " ".join(str(category or "").strip().lower().split())
    return normalized == "tips" or normalized.endswith("tips")


def _content_type(item):
    category = str(item.get("category", "")).lower()
    asset_type = item.get("asset_type")

    if asset_type == "plugin" or "plugin" in category or "プラグイン" in category:
        return "plugin"
    if asset_type == "game" or category in {"ゲーム", "game"}:
        return "game"
    if item.get("source_site_type") == "official" or category in {"公式情報", "公式", "SourceCheck"}:
        return "official"
    if category in {"サイト更新", "sourcecheck"}:
        return "site_update"
    if (
        (isinstance(item.get("development_info_type"), str) and item.get("development_info_type"))
        or asset_type == "development_tool"
        or category.strip() == "開発情報"
        or _is_tips_category(category)
    ):
        return "development_info"
    if asset_type in {"graphic", "sound"}:
        return "asset"
    if any(x in category for x in ("素材", "グラフィック", "サウンド")):
        return "asset"
    return "other"


def _development_info_type(item, content_type):
    allowed = {
        "runtime_player",
        "development_tool",
        "conversion_tool",
        "technical_reference",
        "tutorial",
        "tip",
    }
    value = item.get("development_info_type")
    if isinstance(value, str) and value in allowed:
        return value
    if content_type != "development_info":
        return None
    if item.get("asset_type") == "development_tool":
        return "development_tool"
    if _is_tips_category(item.get("category")):
        return "tip"
    return None


def _normalize_source_timestamp(value):
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)) or (
        isinstance(value, str) and value.strip().isdigit()
    ):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
        except (OverflowError, OSError, TypeError, ValueError):
            return str(value).strip()
    return str(value).strip()


def _normalize_list(value):
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def normalize_item(item, collector_name):
    item = dict(item)
    sites = _load_sites()

    site_record = sites.get(collector_name, {})
    source_site_id = item.get("source_site_id") or site_record.get("source_site_id")
    if not source_site_id:
        source_site_id = "SITE-UNREGISTERED"

    url = str(item.get("url", "")).strip()
    source_item_id = item.get("source_item_id") or item.get("deviationid") or url
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
    item["development_info_type"] = _development_info_type(item, item["content_type"])
    if item["content_type"] == "development_info":
        # Legacy development_tool values are migrated to the dedicated subtype.
        item["asset_type"] = None
    item["source_site_id"] = source_site_id
    item.setdefault("source_site_name", site_record.get("source_site_name"))
    item.setdefault("source_site_type", site_record.get("source_site_type"))
    item["source_site_language"] = _normalize_list(
        item.get("source_site_language", site_record.get("source_site_language", []))
    )
    item.setdefault("source_site_status", site_record.get("source_site_status"))
    item["collector"] = collector_name
    item["source_item_id"] = str(source_item_id)
    item["source"] = item.get("source") or collector_name
    item["url"] = url
    item["title"] = str(item.get("title", "")).strip()

    item["subcategory"] = subcategory
    item["tags"] = tags
    item["languages"] = languages
    item.setdefault("sound_type", None)
    item.setdefault("file_formats", [])
    item.setdefault("graphic_style", [])
    item.setdefault("graphic_theme", [])
    item.setdefault("engine_relevant", None)
    item["plugin_category"] = plugin_category
    item["supported_platforms"] = _normalize_list(item.get("supported_platforms"))
    raw_links = item.get("links")
    item["links"] = [
        dict(link)
        for link in raw_links
        if isinstance(link, dict) and isinstance(link.get("url"), str) and link.get("url").strip()
    ] if isinstance(raw_links, list) else []
    collector_metadata = item.get("collector_metadata")
    if isinstance(collector_metadata, dict) and collector_metadata:
        item["collector_metadata"] = dict(collector_metadata)
    else:
        item.pop("collector_metadata", None)

    item.setdefault("commercial_use", None)
    item.setdefault("credit_required", None)
    item.setdefault("redistribution_allowed", None)

    if item.get("source_published_at") is None:
        published_value = item.get("published_at")
        if published_value is None:
            published_value = item.get("published_time")
        if published_value is not None:
            item["source_published_at"] = _normalize_source_timestamp(published_value)
    elif item.get("source_published_at") is not None:
        item["source_published_at"] = _normalize_source_timestamp(item["source_published_at"])
    item.setdefault("source_updated_at", item.get("updated_at"))
    item.setdefault("first_seen_at", now)
    item.setdefault("collected_at", now)

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
