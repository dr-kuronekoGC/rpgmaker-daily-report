#!/usr/bin/env python3
"""Conservatively resolve only high-confidence non-resource review records.

This script is intentionally stricter than a classifier:
- HTTP 404/410 can establish that the stored page is unavailable.
- Clear direct profile URLs are not individual deliverables.
- Explicit requests/discussions/showcases are excluded only when the page has
  no strong release/download evidence.
- 403/429/5xx/timeouts and parse failures are NEVER treated as dead links.
- Resource type is inferred from title evidence before body/reply text.
- Dead-link exclusion requires a recognized delivery link for a known resource type.
Ambiguous records remain open for human review.
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import fetch_historical_review_bodies as fetcher
from asset_metadata import build_asset_metadata

LEDGER_PATH = Path("data/review/classification_review.json")
LOG_PATH = Path("data/review/auto_screen_log.json")
AUDIT_PATH = Path("data/review/auto_screen_audit.json")
JST = timezone(timedelta(hours=9))

# Avoid long hangs on sites that are currently blocking or timing out.
fetcher.TIMEOUT = 8
fetcher.PAUSE_SECONDS = 0.15

RESOLVED_MARKER_RE = re.compile(r"\b(?:solved|resolved|filled|answered|completed)\b", re.I)
REQUEST_RE = re.compile(
    r"\b(?:looking for|searching for|request(?:ing)?|need(?:ing)?|"
    r"can anyone (?:make|share|provide|create)|anyone have|gimme|give me|"
    r"need help finding|does anyone have|wanted|request for images|image request|"
    r"resource request|sound request|plugin request|please make|could you make|"
    r"can you make|suche|gesucht|kann mir jemand|hat jemand|bitte um|"
    r"cerco|cercasi|richiesta|mi serve|je cherche|recherche|besoin de|aidez-moi)\b"
    r"|(?:ищу|ищем|помогите найти|нужен|нужна|нужны|где найти|素材を探しています|"
    r"素材を探している|素材募集|素材をください|画像をください|画像ください|"
    r"素材ください|作ってください|探しています|探してます|求む|くれくれ)",
    re.I,
)

BODY_REQUEST_RE = re.compile(
    r"\b(?:request\s+(?:withdrawn|cancelled|canceled)|i would (?:very much )?appreciate it if someone could\s+(?:make|share|provide|create|recolor|upload))\b|"
    r"\b(?:please|pls)\s+up\s+(?:the\s+)?(?:[\w-]+\s+){0,5}(?:sheets?|sprites?|tilesets?|graphics|animations?|assets?|resources?|plugins?)\b|"
    r"\b(?:looking for|searching for|request(?:ing)?\s+(?:a|an|some|for)|"
    r"need help finding|can anyone (?:make|share|provide|create)|"
    r"anyone have|does anyone have|help me find|where can i find|"
    r"i am looking for|i'm looking for|seeking (?:a|an|some)|"
    r"can someone (?:make|share|provide|create)|"
    r"could someone (?:make|share|provide|create)|"
    r"je cherche|cerco|cercasi|ищу|ищем|помогите найти|где найти)\b"
    r"|(?:素材を探しています|素材を探している|素材募集|素材をください|"
    r"画像をください|画像ください|素材ください|求む|くれくれ)",
    re.I,
)
DISCUSSION_RE = re.compile(
    r"\b(?:discussion|discuss|what do you think|which is better|"
    r"how do i|how can i|why does|is there a way|question|help with|"
    r"discussione|opinioni|diskussion|meinung|обсуждение|вопрос)\b"
    r"|(?:質問|相談|意見を聞かせて)",
    re.I,
)
SHOWCASE_RE = re.compile(
    r"\b(?:showcase|my game|my project|my works|my lavori|my drawings?|my pixel art|my art|"
    r"work in progress|\bwip\b|development process|making of|screenshots?|gameplay video|"
    r"mapping showcase|battlers?\s+(?:i've drawn|i drew)|my (?:new|first) battlers?|"
    r"my (?:new|first) sprites?|lavori pixel art|pixel art diary|art diary|"
    r"imparando pixel art|cronache di .*pixel artist|diario di pixel art|"
    r"miei lavori|le mie creazioni|il mio progetto|mon projet|mes créations|"
    r"mein projekt|meine arbeiten|мои работы|мой проект|мой арт)"
    r"|(?:作品紹介|制作過程|スクリーンショット|ゲームプレイ動画)",
    re.I,
)
MOVED_TOPIC_RE = re.compile(
    r"^\s*(?:\[?moved\]?\s*[:\-]|moved\s+to\b|"
    r"\[(?:deleted|removed)\]\s*)",
    re.I,
)
FEEDBACK_ONLY_RE = re.compile(
    r"\b(?:which (?:one|style) (?:is )?(?:better|prettier)|what do you think|"
    r"which do you prefer|feedback only|opinions? please|"
    r"quale (?:è|e')?\s*(?:più\s*)?(?:bella|carina|bello|meglio)|"
    r"quale preferite|quale vi piace|secondo voi|cosa ne pensate|che ne pensate|"
    r"opinioni|pareri|"
    r"qu'en pensez-vous|vous préférez|was meint ihr|welche gefällt euch|"
    r"что думаете|какой вариант лучше)\b",
    re.I,
)


NO_DELIVERABLE_RE = re.compile(
    r"\b(?:not a resource|no download|not available for download|"
    r"not for download|just (?:a )?(?:screenshot|preview|showcase)|"
    r"only a preview|not sharing (?:this|these|it)|not a release|"
    r"no files? (?:attached|provided)|made only for my own game|"
    r"no download link|no files provided|not releasing|only screenshots|"
    r"just showing my game|не для скачивания|без скачивания)\b"
    r"|(?:素材配布ではない|配布していません|ダウンロード不可|プレビューのみ|"
    r"スクリーンショットのみ|自分のゲーム専用)",
    re.I,
)
POSITIVE_RELEASE_RE = re.compile(
    r"\b(?:downloadable|download link|download here|release page|"
    r"release available|resource pack|asset pack|sound pack|audio pack|"
    r"pack of sounds|sound archive|archive of sounds|free to use|"
    r"available for use|get it here|mediafire|mega\.nz|dropbox|"
    r"google drive|yadi\.sk|disk\.yandex|yandex\.(?:ru|com)|ya\.ru|"
    r"itch\.io|github\.com|\.zip\b|\.rar\b|\.7z\b|"
    r"\.ogg\b|\.mp3\b|\.wav\b|\.js\b|архив звуков|пак звуков|"
    r"звуковой архив|пак со звуками|ссылка на папку|скачать)",
    re.I,
)
ASSET_WORD_RE = re.compile(
    r"\b(?:sprite|sprites|charset|battler|tileset|tile set|icon pack|"
    r"resource|asset|plugin|script|bgm|bgs|sound effect|music pack|"
    r"animation sheet|sound pack|tool)\b",
    re.I,
)
RESOURCE_LINK_RE = re.compile(
    # Link URLs and anchor labels use different languages across the forums.
    # Include common download/archive/resource terms so old posts with generic
    # file-hosting URLs are not silently skipped by the link audit.
    r"download|descargar|t[eé]l[eé]charger|herunterladen|scarica|scaricare|"
    r"скачать|загрузить|скачиван|downloaden|"
    r"mediafire|mega\.nz|dropbox|drive\.google|google drive|"
    r"yadi\.sk|disk\.yandex|yandex\.(?:ru|com)|ya\.ru|"
    r"\.zip(?:$|[?#])|\.rar(?:$|[?#])|\.7z(?:$|[?#])|"
    r"\.ogg(?:$|[?#])|\.mp3(?:$|[?#])|\.wav(?:$|[?#])|"
    r"\.png(?:$|[?#])|\.jpe?g(?:$|[?#])|\.gif(?:$|[?#])|"
    r"\.js(?:$|[?#])|/downloads?(?:/|$)|/art/|itch\.io|"
    r"github\.com/.*/releases|"
    r"архив|файл|файлы|музык|звуков|ресурс|плагин|спрайт|тайлсет|"
    r"анимац|иконк|материал|скачив|"
    r"download[- ]?link|freebie|asset pack|resource pack|sound pack|"
    r"scaricamento|download gratuit|t[eé]l[eé]chargement|"
    r"herunterladen|datei|ressourcen|materialien|"
    r"descarga|archivo|recursos|"
    r"ダウンロード|配布|素材|添付|ファイル|音源|効果音|BGM|プラグイン",
    re.I,
)
# Check every detected resource link (the page parser caps extracted links at 100).
# This avoids keeping a resource when only the first three of many download links were checked.
MAX_RESOURCE_LINKS = 100
LINK_TIMEOUT = 3

# The user consistently excludes posts whose purpose is only to advertise a
# discount, time-limited sale, coupon, or contest giveaway. A product/store
# URL alone is not evidence that a usable downloadable file is included.
PROMOTION_ONLY_RE = re.compile(
    r"\b(?:limited[- ]time (?:sale|offer|discount|deal)|flash sale|"
    r"time[- ]limited (?:offer|discount|sale)|discount(?:ed)?|coupon|"
    r"promo code|sale ends|on sale|price drop|special offer|"
    r"giveaway contest|enter to win|raffle|"
    r"limited offer|discount code|free for a limited time)\b"
    r"|(?:期間限定(?:セール|割引|販売|配布)|タイムセール|割引クーポン|"
    r"セール終了|抽選プレゼント|抽選でプレゼント|期間限定の割引|"
    r"скидк|распродаж|розыгрыш|только сегодня|"
    r"offerta a tempo limitato|sconto|codice sconto|"
    r"vente flash|offre limitée|réduction|code promo|"
    r"zeitlich begrenz(?:t|te) (?:Angebot|Rabatt)|Rabattcode)",
    re.I,
)
DIRECT_DOWNLOAD_RE = re.compile(
    r"download|descargar|t[eé]l[eé]charger|herunterladen|scarica|scaricare|"
    r"скачать|загрузить|mediafire|mega\.nz|dropbox|drive\.google|"
    r"google drive|yadi\.sk|disk\.yandex|yandex\.(?:ru|com)|ya\.ru|"
    r"\.(?:zip|rar|7z|ogg|mp3|wav|js)(?:$|[?#])|/downloads?(?:/|$)|"
    r"ダウンロード|添付ファイル|ファイルをダウンロード",
    re.I,
)


def has_direct_download_link(link_check: dict) -> bool:
    for result in link_check.get("results") or []:
        if DIRECT_DOWNLOAD_RE.search(clean(result.get("url"))) or DIRECT_DOWNLOAD_RE.search(clean(result.get("text"))):
            return True
    return False


RESOURCE_FILE_SUFFIXES = {
    ".zip", ".rar", ".7z", ".gz", ".tar", ".tgz", ".ogg", ".mp3", ".wav",
    ".m4a", ".mid", ".midi", ".flac", ".js", ".mjs", ".rb", ".json",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp",
}
RESOURCE_HOST_RE = re.compile(
    r"(?:mediafire\.com|mega\.nz|dropbox\.com|drive\.google\.com|"
    r"yadi\.sk|disk\.yandex|yandex\.(?:ru|com)|itch\.io|"
    r"raw\.githubusercontent\.com|github\.com/.*/(?:releases|archive))",
    re.I,
)


def is_resource_candidate_link(url: str, label: str) -> bool:
    """Recognize file links even when the anchor text is generic or untranslated."""
    parsed = urlparse(url)
    suffix = Path(parsed.path.rstrip("/")).suffix.lower()
    if suffix in RESOURCE_FILE_SUFFIXES or RESOURCE_HOST_RE.search(url):
        return True
    return bool(RESOURCE_LINK_RE.search(url) or RESOURCE_LINK_RE.search(label))


def check_resource_links(session, page: dict, source_url: str) -> dict:
    """Check likely resource links, including generic-labelled file hosts."""
    candidates = []
    seen = set()
    for link in page.get("outbound_links") or []:
        if not isinstance(link, dict):
            continue
        target = clean(link.get("url"))
        label = clean(link.get("text"))
        if not target.startswith(("http://", "https://")) or target in seen:
            continue
        if not is_resource_candidate_link(target, label):
            continue
        seen.add(target)
        candidates.append({
            "text": label[:160],
            "url": target,
            # Preserve how the parser found this URL. Image-host evidence is only
            # trusted for images inside post content, never arbitrary links.
            "link_kind": clean(link.get("link_kind")) or "anchor",
        })
    if not candidates:
        return {"candidate_count": 0, "checked_count": 0, "all_checked_dead": False, "results": []}

    checked = []
    for candidate in candidates[:MAX_RESOURCE_LINKS]:
        status = None
        method = "HEAD"
        error = None
        try:
            response = session.head(
                candidate["url"], allow_redirects=True, timeout=LINK_TIMEOUT,
                headers={"User-Agent": fetcher.USER_AGENT},
            )
            status = response.status_code
            response.close()
            if status in {403, 405, 501}:
                method = "GET"
                response = session.get(
                    candidate["url"], allow_redirects=True, timeout=LINK_TIMEOUT,
                    headers={"User-Agent": fetcher.USER_AGENT}, stream=True,
                )
                status = response.status_code
                response.close()
        except fetcher.requests.RequestException as exc:
            error = type(exc).__name__
        checked.append({
            **candidate,
            "http_status": status,
            "method": method,
            "error": error,
            "dead": status in {404, 410},
            "reachable": status is not None and 200 <= status < 400,
        })

    all_dead = (
        len(candidates) <= MAX_RESOURCE_LINKS
        and len(checked) == len(candidates)
        and bool(checked)
        and all(result["dead"] for result in checked)
    )
    return {
        "candidate_count": len(candidates),
        "checked_count": len(checked),
        "all_checked_dead": all_dead,
        "results": checked,
    }


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def is_direct_profile(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/").lower()
    host = (parsed.hostname or "").lower()
    if re.search(r"/(?:forum/)?(?:user|users|profile|profiles|members)/[^/]+$", path):
        return True
    # DeviantArt artist landing pages are profiles; individual works use /art/.
    if host.endswith("deviantart.com") and path.count("/") == 1 and "/art/" not in path:
        return True
    # itch.io creator landing pages, not individual project pages.
    if host.endswith(".itch.io") and path in {"", "/"}:
        return True
    return False



AUDIO_RESOURCE_RE = re.compile(
    r"\b(?:music|musics|musica|musiche|audio|soundtrack|soundtracks|"
    r"sound pack|audio pack|bgm|bgs|sound effects|album|albums)\b"
    r"|(?:музык|саундтрек|звуков|аудио|альбом|треки|музыка|"
    r"музыкальн|архив звуков|пак звуков|musica|musiche|suono|suoni|"
    r"effetti sonori|colonna sonora|traccia sonora)",
    re.I,
)
PLUGIN_RESOURCE_RE = re.compile(
    r"\b(?:plugins?|scripts?|rgss|javascript|\.js)\b"
    r"|(?:плагин|скрипт|плагины)",
    re.I,
)
GRAPHICS_RESOURCE_RE = re.compile(
    r"\b(?:sprites?|spritesheets?|charset|charsets|tilesets?|tile sets?|"
    r"battlers?|icons?|icon pack|icon set|animation sheets?|"
    r"graphics|art material|free art material|resource pack|asset pack|"
    r"resources?|doodads|character generator|butterfly|butterflies)\b"
    r"|(?:free[-_]art[-_]material|art[-_]material|resource[-_]pack|asset[-_]pack|sound[-_]pack|icon[-_]pack)"
    r"|(?:ресурс|спрайт|тайлсет|график|анимац|иконк|набор иконок|"
    r"персонаж|бабочк|материал|графика|ресурсы|пакет ресурсов|"
    r"объединённые ресурсы|объединенные ресурсы|"
    r"icone|icona|grafica|materiali|risorse|animazioni|personaggi|"
    r"素材|配布|タイルセット|キャラセット|スプライト|アイコン|アニメーション)",
    re.I,
)
RESOURCE_TITLE_RE = re.compile(
    r"\b(?:resource staff releases pack|sprites?|spritesheets?|charset|charsets|"
    r"tilesets?|tile sets?|battlers?|icons?|icon pack|icon set|"
    r"animation sheets?|graphics|art material|free art material|"
    r"resource pack|asset pack|resources?|doodads|character generator|"
    r"soundtracks?|music|musics|musica|musiche|audio|sound pack|audio pack|"
    r"bgm|bgs|plugins?|scripts?|butterfly|butterflies)\b"
    r"|(?:ресурс|спрайт|тайлсет|музык|саундтрек|звуков|аудио|альбом|"
    r"архив звуков|пак звуков|анимац|иконк|набор иконок|бабочк|"
    r"график|материал|ресурсы|объединённые ресурсы|объединенные ресурсы|"
    r"musica|musiche|suoni|effetti sonori|colonna sonora|traccia sonora|"
    r"icone|icona|grafica|materiali|risorse|animazioni|personaggi|"
    r"butterfl(?:y|ies)|free[-_]art[-_]material|art[-_]material|"
    r"resource[-_]pack|asset[-_]pack|sound[-_]pack|icon[-_]pack|"
    r"素材|配布|タイルセット|キャラセット|スプライト|アイコン|アニメーション|"
    r"音源|効果音|プラグイン|BGM|BGS)",
    re.I,
)

NON_RESOURCE_TITLE_RE = re.compile(
    r"\b(?:looking for|request|help me find|question|discussion|tutorial|"
    r"how to|how do i|showcase|work in progress|wip|my game|gameplay|"
    r"ideas and implementation|feedback please|for feedback only)\b"
    r"|(?:ищу|помогите найти|вопрос|обсуждение|ищется|"
    r"質問|相談|素材を探しています|素材をください)",
    re.I,
)
PREVIEW_FILE_RE = re.compile(
    r"(?:^|[/_. -])(?:screenshot|screen[-_ ]?shot|preview|thumb(?:nail)?|"
    r"logo|avatar|cover|sample)(?:[/_. -]|$)",
    re.I,
)
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
SEMANTIC_ATTACHMENT_FILENAME_RE = re.compile(
    r"(?:charset|tileset|sprite|battler|icon|butterfl|animation|resource|asset|"
    r"персонаж|бабочк|спрайт|тайлсет|иконк|анимац)",
    re.I,
)
DELIVERABLE_EXTENSIONS = {
    ".zip", ".rar", ".7z", ".gz", ".tar", ".ogg", ".mp3", ".wav",
    ".m4a", ".mid", ".midi", ".flac", ".js", ".mjs", ".rb", ".json",
}


def resource_kind(title: str, body: str) -> str | None:
    """Infer type from the title first; noisy replies/footer text cannot override it."""
    title = clean(title)
    body = clean(body)

    if AUDIO_RESOURCE_RE.search(title):
        return "audio"
    if PLUGIN_RESOURCE_RE.search(title):
        return "plugin"

    graphics_specific = re.compile(
        r"\b(?:sprites?|spritesheets?|charset|charsets|tilesets?|tile sets?|"
        r"battlers?|icons?|icon pack|icon set|animation sheets?|graphics|"
        r"doodads|character generator|butterflies?)\b"
        r"|(?:спрайт|тайлсет|график|анимац|иконк|набор иконок|персонаж|бабочк|"
        r"icone|icona|grafica|materiali|risorse|animazioni|personaggi|"
        r"素材|タイルセット|キャラセット|スプライト|アイコン|アニメーション)",
        re.I,
    )
    if graphics_specific.search(title):
        return "graphics"

    if re.search(
        r"\b(?:resource staff releases pack|resources?|resource pack|asset pack|"
        r"humble|gamedev resources?)\b|(?:ресурс(?:ы|ов)?|объединённые ресурсы|"
        r"объединенные ресурсы)",
        title,
        re.I,
    ):
        return "resource"

    # Only use the opening body section when the title has no resource type,
    # and only if exactly one concrete type is present. Long forum threads
    # often contain replies/signatures that mention unrelated resource types.
    opening = body[:700]
    kinds = []
    if AUDIO_RESOURCE_RE.search(opening):
        kinds.append("audio")
    if PLUGIN_RESOURCE_RE.search(opening):
        kinds.append("plugin")
    if graphics_specific.search(opening):
        kinds.append("graphics")
    return kinds[0] if len(kinds) == 1 else None


def is_delivery_link(result: dict, kind: str | None) -> bool:
    """Distinguish downloadable assets from preview images and ordinary links."""
    url = clean(result.get("url"))
    if not url.startswith(("http://", "https://")):
        return False
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path = parsed.path.lower()
    suffix = Path(parsed.path).suffix.lower()

    # Legacy image hosts such as Photobucket store the actual image filename
    # in a query parameter (for example ?action=view&current=charset.png),
    # while the URL path itself has no image extension. Recognize only known
    # image extensions in known filename-like parameters; never infer a file
    # type from an arbitrary query string.
    query_image_filename = False
    if suffix not in IMAGE_EXTENSIONS:
        query = parse_qs(parsed.query)
        for key in ("current", "file", "filename", "image", "photo"):
            values = query.get(key, [])
            found_suffix = next(
                (
                    Path(urlparse(unquote(value)).path).suffix.lower()
                    for value in values
                    if Path(urlparse(unquote(value)).path).suffix.lower() in IMAGE_EXTENSIONS
                ),
                None,
            )
            if found_suffix:
                suffix = found_suffix
                query_image_filename = True
                break

    if suffix in DELIVERABLE_EXTENSIONS:
        return True

    # Legacy RMRK attachments use a PHP endpoint with an opaque numeric ID
    # (for example, index.php?action=dlattach;topic=38714.0;attach=20424),
    # so the URL extension does not reveal the file type. Use the visible
    # attachment filename plus the known endpoint as evidence; never treat
    # generic forum images or profile pictures as deliverable assets.
    legacy_attachment = (
        host in {"rmrk.net", "www.rmrk.net"}
        and re.search(r"(?:[?;&])action=dlattach(?:[;&]|$)", url, re.I)
        and re.search(r"(?:[?;&])attach=\d+", url, re.I)
    )
    label_suffix = Path(urlparse(clean(result.get("text"))).path).suffix.lower()
    label = clean(result.get("text"))
    if legacy_attachment:
        if label_suffix in DELIVERABLE_EXTENSIONS:
            return True
        if (
            kind in {"graphics", "mixed", "resource"}
            and label_suffix in IMAGE_EXTENSIONS
            and not PREVIEW_FILE_RE.search(label)
            and result.get("link_kind") in {"image_anchor", "anchor"}
        ):
            return True

    # In an audio post, cover art and screenshots do not prove that audio files survive.
    if suffix in IMAGE_EXTENSIONS:
        if kind == "audio":
            return False
        filename = Path(parsed.path).name
        if re.search(
            r"/(?:themes?/|avatars?/|ranks?/|medals?/|images/post/|smilies/|emoticons?/|users?/avatar)",
            path,
            re.I,
        ):
            return False
        if PREVIEW_FILE_RE.search(path):
            return False
        if "/attachments/" in path and SEMANTIC_ATTACHMENT_FILENAME_RE.search(filename):
            return True

        # Older resource forums often host actual battler/sprite images on
        # image-sharing sites instead of their own attachment directory.
        image_hosts = (
            "imageshack.us", "photobucket.com", "imgur.com", "postimg.cc",
            "postimg.org", "ibb.co", "imagebam.com", "imgbox.com",
        )
        if (
            (result.get("link_kind") in {"image_anchor", "embedded_image", "anchor", "plain_text_url"} or query_image_filename)
            and any(host == domain or host.endswith("." + domain) for domain in image_hosts)
            and kind in {"graphics", "resource", "mixed"}
        ):
            return True
        return False


    # Known file-sharing destinations. Ignore Yandex image-view URLs (/i/).
    if host == "yadi.sk" and path.startswith("/d/"):
        return True
    if host.endswith("yandex.ru") and path.startswith("/d/"):
        return True
    if host == "drive.google.com" and (
        path.startswith("/file/d/") or path == "/open" or path.startswith("/drive/folders")
    ):
        return True
    if host.endswith(("mediafire.com", "mega.nz", "dropbox.com")):
        return True
    if host.endswith("itch.io"):
        return bool(re.search(r"(?:asset|art|sprite|tile|resource|music|sound|plugin|pack|material|graphics)", path, re.I))
    if host == "raw.githubusercontent.com":
        return True
    if host == "github.com" and re.search(r"/(?:releases|archive)/|\.(?:js|mjs|rb|zip)(?:$|/)", path, re.I):
        return True
    return False


def delivery_link_summary(title: str, body: str, link_check: dict) -> dict:
    kind = resource_kind(title, body)
    results = [
        result for result in (link_check.get("results") or [])
        if isinstance(result, dict) and is_delivery_link(result, kind)
    ]
    return {
        "resource_kind": kind,
        "candidate_count": len(results),
        "reachable_count": sum(bool(result.get("reachable")) for result in results),
        "dead_count": sum(bool(result.get("dead")) for result in results),
        "error_count": sum(bool(result.get("error")) or result.get("http_status") is None for result in results),
        "results": results,
    }


def confirmed_resource_decision(title: str, body: str, link_check: dict) -> tuple[str, str] | None:
    """Confirm only an unmistakable asset/plugin post with a live delivery link."""
    # Reject explicit request/discussion titles, but do not let incidental
    # words in a resource description (e.g. "tutorial", "how to", "feedback")
    # override a live downloadable asset. Showcase titles may still be reusable
    # resources when an actual asset file is reachable.
    if NON_RESOURCE_TITLE_RE.search(title):
        return None
    if DISCUSSION_RE.search(title):
        return None
    summary = delivery_link_summary(title, body, link_check)
    live = [result for result in summary["results"] if result.get("reachable")]
    if not live:
        return None

    # A creator/profile title may be generic while its linked product page clearly
    # identifies the asset (for example, an itch.io "free-art-material" page).
    link_text = " ".join(
        f"{clean(result.get('text'))} {clean(result.get('url'))}"
        for result in live
    )
    kind = resource_kind(title, body) or resource_kind(f"{title}\n{link_text}", body)
    if not kind:
        return None

    # Some older forum topics use creative titles without naming the asset type.
    # When the first post clearly identifies one resource type and at least three
    # independent, recognized delivery links are live, that combination is strong
    # enough to confirm without a resource keyword in the title or URL labels.
    body_kind = resource_kind("", body[:1800])
    multiple_live_deliveries_with_body_evidence = (
        body_kind in {"audio", "plugin", "graphics"}
        and len(live) >= 3
    )
    title_or_link_evidence = bool(
        RESOURCE_TITLE_RE.search(title)
        or RESOURCE_TITLE_RE.search(link_text)
        or re.search(r"(?:free-art-material|resource-pack|asset-pack|sound-pack|icon-pack)", link_text, re.I)
        or multiple_live_deliveries_with_body_evidence
    )
    if not title_or_link_evidence:
        return None

    if kind == "plugin":
        return ("plugin", "投稿のタイトル／配布先がプラグイン・スクリプトを示し、取得先リンクがHTTP到達可能")
    if kind == "audio":
        return ("confirmed", "投稿が音楽・音声素材を示し、音声／配布先リンクがHTTP到達可能")
    return ("confirmed", "投稿がグラフィック等の素材を示し、素材ファイルまたは配布先リンクがHTTP到達可能")


def all_delivery_links_dead(title: str, body: str, link_check: dict) -> bool:
    """Only classify dead links when the post's resource type is supported by evidence."""
    summary = delivery_link_summary(title, body, link_check)
    results = summary["results"]
    if not summary["resource_kind"]:
        return False
    return bool(results) and all(
        result.get("dead")
        and not result.get("error")
        and result.get("http_status") in {404, 410}
        for result in results
    )


def classify_page(item: dict, page: dict) -> tuple[str, str] | None:
    url = clean(item.get("url"))
    title = clean(page.get("page_title") or item.get("title"))
    body = clean(page.get("body_text") or page.get("page_description"))
    combined = f"{title}\n{body}"
    status = page.get("http_status")
    retrieval = page.get("retrieval_status")
    link_check = page.get("resource_link_check") or {}

    # Preserve explicit human corrections before applying any automatic rule,
    # including link-death rules. Human review takes precedence over heuristics.
    human_reopen_note = clean(item.get("review_note"))
    if re.search(
        r"(?:自動判定を取り消し|自動除外を取り消し|除外判定を取り消し|未確認に戻す|再確認対象として残す)",
        human_reopen_note,
    ):
        return None

    if status in {404, 410}:
        return ("not_applicable", f"保存されたURLがHTTP {status}を返し、現在ページを取得できない")
    if is_direct_profile(url):
        return ("not_applicable", "個別の素材・配布物ではなく、ユーザープロフィールへの直リンク")
    # Generic links alone cannot prove the resource is gone: a dead preview
    # image is not evidence that the downloadable asset is unavailable.
    # The resource-kind-aware all_delivery_links_dead check below is authoritative.

    if retrieval != "body_found" or not body:
        # A blank/blocked response is not evidence of absence.
        return None

    # For asset-specific posts, evaluate actual delivery links by resource type.
    # A live cover image must not keep a music post open when every track/download
    # link is conclusively dead; timeouts and blocked links still prevent exclusion.
    if all_delivery_links_dead(title, body, link_check):
        return (
            "not_applicable",
            "素材種別に対応する配布先リンクがすべてHTTP 404/410。画像プレビュー等の別種リンクは配布可能な素材として数えない",
        )

    # A live, resource-specific delivery link is itself positive evidence.
    # This prevents a request/discussion keyword from overriding a real file.
    # Distinguish usable resource links from profile photos, preview images,
    # and generic forum chrome before using link status as classification evidence.
    delivery_summary = delivery_link_summary(title, body, link_check)
    has_usable_delivery = delivery_summary["candidate_count"] > 0
    positive_release = bool(
        POSITIVE_RELEASE_RE.search(combined)
        or delivery_summary["reachable_count"] > 0
    )
    resolved_marker = bool(RESOLVED_MARKER_RE.search(title))

    # A personal-art/showcase topic with no usable asset link is not a resource
    # listing. The raw link audit may contain profile avatars, theme icons, or
    # other forum chrome; those are not material links and must not keep a
    # personal showcase in the review queue.
    if SHOWCASE_RE.search(title) and not has_usable_delivery:
        return (
            "not_applicable",
            "個人作品・制作過程の紹介と判断でき、再利用できる素材配布先・埋め込み素材を確認できない（プロフィール画像等は除外）",
        )

    # A post that explicitly asks for opinions on which version looks better
    # is discussion, not a reusable asset listing, when it has no usable material
    # link. Any live resource-specific link or explicit release evidence protects it.
    feedback_only = bool(FEEDBACK_ONLY_RE.search(body[:1200]) or FEEDBACK_ONLY_RE.search(title))
    if feedback_only and not has_usable_delivery and not positive_release:
        return (
            "not_applicable",
            "本文が見た目の比較・意見募集を主目的としており、取得可能な素材配布先を確認できない",
        )

    # A topic explicitly marked as moved/removed is not a useful catalog entry
    # when no replacement resource link is available. If a usable resource link
    # exists, leave it open/eligible even when the original forum topic moved.
    if MOVED_TOPIC_RE.search(title) and not has_usable_delivery:
        return (
            "not_applicable",
            "元投稿が移転・削除扱いで、素材として利用できる配布先リンクも確認できない",
        )
    # Exclude only explicit promotion/discount/contest announcements when the
    # post has no direct downloadable destination. Ordinary paid assets and
    # external storefront links are not excluded by themselves.
    promotion_context = f"{title}\n{body[:1800]}"
    if PROMOTION_ONLY_RE.search(promotion_context) and not has_direct_download_link(link_check):
        return (
            "not_applicable",
            "過去の確認方針に基づき、割引・期間限定セール・抽選告知が主目的で、直接取得できる素材ファイルへのリンクを確認できないため除外",
        )

    # Explicitly ripped/pirated material remains excluded even when a live
    # download link exists. A working link proves availability, not permission
    # to redistribute. Do not use franchise names alone as a piracy signal.
    piracy_evidence = f"{title}\n{body[:1200]}"
    explicit_piracy = bool(re.search(
        r"(?:\[\s*pirate\s*\]|\b(?:pirated|piracy|ripped from|ripped music|"
        r"stolen from|unauthorized rip|(?:audio|music|soundtrack|sound effects?)\s+rip(?:ped)?)\b|"
        r"\bripp(?:ata|ato|ati|ate)\b)",
        piracy_evidence,
        re.I,
    ))
    if explicit_piracy:
        return ("exclude", "海賊版・既存作品からのリッピングを明示する投稿で、公開対象の独自素材として扱えない")

    if NO_DELIVERABLE_RE.search(combined) and not positive_release:
        return ("not_applicable", "本文に素材配布ではない／ダウンロード不可／プレビューのみと明記されている")

    # A solved/filled thread may contain a useful answer or an attached asset.
    # But when it began as a resource request, has no positive release evidence,
    # and has no usable delivery link, it is safe to resolve as a non-resource.
    # Non-request solved topics remain open because the solution may itself be useful.
    if resolved_marker and not has_usable_delivery:
        resolved_request_signal = bool(
            REQUEST_RE.search(title) or BODY_REQUEST_RE.search(body[:1800])
        )
        if resolved_request_signal and not positive_release:
            return (
                "not_applicable",
                "解決済み・充足済みの素材依頼だが、配布根拠および利用可能な素材リンクを確認できない",
            )
        return None

    # Requests for a resource are excluded only when the post itself contains
    # no release/download evidence. Ambiguous threads remain open.
    # Broad words such as "need" or "gimme" are safe in a title, but in
    # a thread body they often appear in offers/replies on genuine resource
    # posts (e.g. "if you need a piece, send me the sheet music"). Require
    # explicit seeking/request phrasing in body text to avoid false exclusions.
    request_signal = bool(REQUEST_RE.search(title) or BODY_REQUEST_RE.search(body[:1800]))
    if request_signal and not positive_release and not has_usable_delivery:
        return ("not_applicable", "素材・プラグイン等を求める依頼投稿で、配布根拠および素材ファイル／配布先リンクを確認できない")

    # Generic discussion/question/showcase language alone is too weak.
    # Require explicit non-deliverable context and no release evidence.
    non_asset_context = bool(DISCUSSION_RE.search(title) or SHOWCASE_RE.search(title))
    explicit_no_release = bool(re.search(
        r"\b(?:just asking|question only|discussion only|not released|"
        r"no files attached|not sharing|for feedback only|showing my game only)\b",
        body[:2200], re.I
    ))
    if non_asset_context and explicit_no_release and not positive_release:
        return ("not_applicable", "質問・議論・作品紹介のみで、本文にも配布物がないことが明示されている")

    # Confirm obvious assets as well as excluding obvious non-resources.
    # This is intentionally limited to a resource-specific title/body plus a
    # live, recognizable download/attachment destination; requests, showcases,
    # and unresolved threads remain for manual review.
    confirmed = confirmed_resource_decision(title, body, link_check)
    request_signal_for_confirmation = bool(
        REQUEST_RE.search(title) or BODY_REQUEST_RE.search(body[:1800])
    )
    if confirmed and not request_signal_for_confirmation:
        return confirmed

    # Reuse the project's established resource-intent classifier against
    # the freshly fetched page text. Only act on explicit high-confidence
    # non-resource results, or medium-confidence question/request/showcase
    # signals; positive distribution evidence always keeps the item open.
    candidate = dict(item)
    candidate["body_text"] = body
    candidate["description"] = clean(page.get("page_description"))
    try:
        triage = build_asset_metadata(candidate)
        intent = triage.get("resource_intent")
        confidence = triage.get("resource_intent_confidence")
        evidence = triage.get("resource_intent_evidence") or []
        signals = {
            entry.get("signal")
            for entry in evidence
            if isinstance(entry, dict)
        }
        if intent == "not_resource" and not positive_release and not has_usable_delivery:
            if confidence == "high":
                return ("not_applicable", "既存の素材意図分類器が高確度で素材・配布物ではないと判定")
            if confidence == "medium" and signals.intersection({
                "question_or_showcase_title",
                "request_or_question_slug",
                "non_resource_category",
            }):
                return ("not_applicable", "既存の素材意図分類器が質問・依頼・作品紹介を検出し、本文にも配布根拠がない")
    except Exception:
        # A classifier error is not evidence that an item should be excluded.
        pass

    # Copyrighted franchise names without an explicit piracy indicator are
    # intentionally not auto-excluded.
    return None


def main() -> int:
    try:
        ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[Auto screen] Cannot read ledger: {exc}", file=sys.stderr)
        return 2

    items = ledger.get("items")
    if not isinstance(items, list):
        print("[Auto screen] Invalid review ledger: expected items list", file=sys.stderr)
        return 2

    open_items = [x for x in items if isinstance(x, dict) and x.get("status") == "open"]
    session = fetcher.requests.Session()
    session.headers.update({"User-Agent": fetcher.USER_AGENT})
    now = datetime.now(JST).isoformat(timespec="seconds")
    log = []
    resolved = []
    audit_rows = []

    for index, item in enumerate(open_items, start=1):
        page = fetcher.fetch_item(session, item)
        # Discourse's JSON endpoint can fail while the ordinary topic page
        # still works. Verify the original URL before treating JSON 404/410
        # as a dead link.
        if page.get("retrieval_method") == "discourse_json" and page.get("http_status") in {404, 410}:
            try:
                html_page = fetcher.parse_html(session, clean(item.get("url")))
                page.update(html_page)
                page["retrieval_status"] = fetcher.body_retrieval_status(page)
            except fetcher.requests.HTTPError as exc:
                actual_status = exc.response.status_code if exc.response is not None else None
                if actual_status not in {404, 410}:
                    page["http_status"] = actual_status
                    page["retrieval_status"] = "unavailable"
            except fetcher.requests.RequestException:
                # An unverified HTML retry is not proof that the link is dead.
                page["http_status"] = None
                page["retrieval_status"] = "unavailable"
        page["resource_link_check"] = check_resource_links(session, page, clean(item.get("url")))
        outcome = classify_page(item, page)
        current_title = clean(page.get("page_title") or item.get("title"))
        current_body = clean(page.get("body_text") or page.get("page_description"))
        delivery_summary = delivery_link_summary(
            current_title, current_body, page.get("resource_link_check") or {}
        )
        combined_text = f"{current_title}\n{current_body[:1800]}"
        triage_signals = {
            "title_resource_signal": bool(RESOURCE_TITLE_RE.search(current_title)),
            "request_signal": bool(REQUEST_RE.search(current_title) or BODY_REQUEST_RE.search(current_body[:1800])),
            "discussion_or_showcase_signal": bool(DISCUSSION_RE.search(current_title) or SHOWCASE_RE.search(current_title)),
            "explicit_no_deliverable": bool(NO_DELIVERABLE_RE.search(combined_text)),
            "positive_release_signal": bool(POSITIVE_RELEASE_RE.search(combined_text)),
            "resource_kind": resource_kind(current_title, current_body),
            "delivery_links_live": delivery_summary["reachable_count"],
            "delivery_links_dead": delivery_summary["dead_count"],
            "delivery_links_errors": delivery_summary["error_count"],
            "body_characters": len(current_body),
            "source_tags": page.get("source_tags") or [],
        }
        audit_rows.append({
            "pre_id": item.get("pre_id"),
            "source": item.get("source"),
            "title": clean(item.get("title"))[:300],
            "url": clean(item.get("url")),
            "http_status": page.get("http_status"),
            "retrieval_status": page.get("retrieval_status"),
            "retrieval_method": page.get("retrieval_method"),
            "retrieval_error": page.get("retrieval_error"),
            # Parser diagnostics are essential when a page returns HTTP 200 but
            # no post body: distinguish missing selectors from a challenge page.
            "html_diagnostics": page.get("html_diagnostics"),
            "resource_link_check": page.get("resource_link_check"),
            "delivery_link_check": delivery_summary,
            "html_diagnostics": page.get("html_diagnostics"),
            "triage_signals": triage_signals,
            "suggestion": outcome[0] if outcome else "keep_open",
            "reason": outcome[1] if outcome else "",
        })
        print(
            f"[Auto screen] {index}/{len(open_items)} {item.get('pre_id')} "
            f"http={page.get('http_status')} retrieval={page.get('retrieval_status')} "
            f"decision={outcome[0] if outcome else 'keep_open'}"
        )
        if outcome:
            decision, reason = outcome
            evidence = {
                "method": "automated_screening_v1",
                "checked_at": now,
                "http_status": page.get("http_status"),
                "retrieval_status": page.get("retrieval_status"),
                "page_title": clean(page.get("page_title"))[:300],
                "html_diagnostics": page.get("html_diagnostics"),
                "reason": reason,
                "resource_link_check": page.get("resource_link_check"),
                "delivery_link_check": delivery_link_summary(
                    clean(page.get("page_title") or item.get("title")),
                    clean(page.get("body_text") or page.get("page_description")),
                    page.get("resource_link_check") or {},
                ),
            }
            item["status"] = "resolved"
            item["decision"] = decision
            item["resolved_at"] = now
            item["review_note"] = f"自動スクリーニング（高確度）: {reason}。取得状況: HTTP {page.get('http_status') or '不明'} / {page.get('retrieval_status') or '不明'}。"
            item["resolution_method"] = "automated_screening_v1"
            item["resolution_evidence"] = evidence
            resolved.append(item["pre_id"])
            log.append({"pre_id": item.get("pre_id"), "url": item.get("url"), **evidence, "decision": decision})
        time.sleep(fetcher.PAUSE_SECONDS)

    audit_payload = {
        "schema_version": 1,
        "checked_at": now,
        "scanned_item_count": len(audit_rows),
        "auto_resolved_count": len(resolved),
        "note": "Latest pass over items that were open at scan start. HTTP 403/429/5xx, timeouts, and ambiguous resource links are not treated as dead links.",
        "items": audit_rows,
    }
    AUDIT_PATH.write_text(json.dumps(audit_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not resolved:
        print(f"[Auto screen] No high-confidence exclusions. {len(open_items)} items remain open.")
        print(f"[Auto screen] Wrote link/retrieval audit for {len(audit_rows)} items.")
        return 0

    LEDGER_PATH.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    previous = []
    if LOG_PATH.exists():
        try:
            payload = json.loads(LOG_PATH.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                previous = payload
        except json.JSONDecodeError:
            print("[Auto screen] Existing log is invalid JSON; refusing to overwrite it.", file=sys.stderr)
            return 2
    LOG_PATH.write_text(json.dumps(previous + log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[Auto screen] Resolved: {len(resolved)} / {len(open_items)} open items")
    print("[Auto screen] Resolved PRE IDs: " + ", ".join(resolved))
    print("[Auto screen] Ambiguous, blocked, and temporary failures remain open.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
