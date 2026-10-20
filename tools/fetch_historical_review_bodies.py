#!/usr/bin/env python3
"""Fetch publicly accessible page text for already-reviewed historical items.

Audit-only: never modifies the review ledger, archive, seen state, or runtime
classification. Output contains short text excerpts and retrieval diagnostics.
"""
from __future__ import annotations

import ipaddress
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

LEDGER_PATH = Path("data/review/classification_review.json")
OUTPUT_PATH = Path("historical_review_bodies.json")
MAX_ITEMS = 106
MAX_BODY_CHARS = 6000
TIMEOUT = 15
PAUSE_SECONDS = 0.6
USER_AGENT = (
    "RPGMakerDailyReport-HistoricalAudit/1.0 "
    "(read-only classification audit; public page text only)"
)


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def is_public_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False
        host = parsed.hostname.lower()
        if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
            return False
        try:
            ip = ipaddress.ip_address(host)
            if not ip.is_global:
                return False
        except ValueError:
            pass
        return True
    except (TypeError, ValueError):
        return False


def extract_links(node, base_url: str) -> list[dict[str, str]]:
    """Extract a bounded list of links from the main post body, not site navigation."""
    links = []
    seen = set()
    if node is None:
        return links
    for anchor in node.select("a[href]"):
        href = urljoin(base_url, str(anchor.get("href") or "").strip())
        parsed = urlparse(href)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or href in seen:
            continue
        # Ignore clickable forum chrome icons (avatars, ranks, medals, and theme
        # buttons); they are not material links even when they end in .png/.gif.
        if anchor.select_one("img[src]") and re.search(
            r"/(?:themes?/|avatars?/|ranks?/|medals?/|images/post/|smilies/|emoticons?/|users?/avatar|uploads/profile/|profile/(?:photo|avatar))",
            parsed.path,
            re.I,
        ):
            continue
        seen.add(href)
        links.append({
            "text": clean_text(anchor.get_text(" ", strip=True))[:160],
            "url": href[:2000],
            "link_kind": "image_anchor" if anchor.select_one("img[src]") else "anchor",
        })
        if len(links) >= 100:
            return links

    # Some music forums embed downloadable tracks in HTML5 <audio> elements
    # rather than ordinary anchors. Capture only explicit audio src/source URLs;
    # a later resource-link check still decides whether the URL is reachable.
    for audio_node in node.select("audio[src], audio source[src]"):
        href = urljoin(base_url, str(audio_node.get("src") or "").strip())
        parsed = urlparse(href)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or href in seen:
            continue
        seen.add(href)
        label = clean_text(audio_node.get("title") or audio_node.get("type") or "")
        links.append({
            "text": (label or "embedded audio source")[:160],
            "url": href[:2000],
            "link_kind": "media_source",
        })
        if len(links) >= 100:
            return links

    # Older forum posts sometimes embed asset images directly without anchors.
    # Capture them as evidence, while downstream checks still require semantic
    # attachment filenames to distinguish assets from random previews.
    for image_node in node.select("img[src]"):
        href = urljoin(base_url, str(image_node.get("src") or "").strip())
        parsed = urlparse(href)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or href in seen:
            continue
        if re.search(
            r"/(?:themes?/|avatars?/|ranks?/|medals?/|images/post/|smilies/|emoticons?/|users?/avatar|uploads/profile/|profile/(?:photo|avatar))",
            parsed.path,
            re.I,
        ):
            continue
        seen.add(href)
        label = clean_text(image_node.get("alt") or image_node.get("title") or "")
        links.append({
            "text": (label or "embedded image/attachment")[:160],
            "url": href[:2000],
            "link_kind": "embedded_image",
        })
        if len(links) >= 100:
            break
    return links


def parse_reddit_json(session: requests.Session, url: str) -> dict:
    endpoint = url.rstrip("/") + ".json"
    response = session.get(
        endpoint,
        params={"raw_json": 1},
        timeout=TIMEOUT,
        headers={"Accept": "application/json"},
    )
    response.raise_for_status()
    data = response.json()
    post = data[0]["data"]["children"][0]["data"]
    selftext = str(post.get("selftext", "") or "")
    markdown_links = [
        {"text": clean_text(label), "url": target}
        for label, target in re.findall(r"\[([^\]]+)\]\((https?://[^)]+)\)", selftext)
    ]
    destination = clean_text(post.get("url_overridden_by_dest") or "")
    if destination.startswith(("http://", "https://")):
        markdown_links.append({"text": "post destination", "url": destination})
    return {
        "retrieval_method": "reddit_json",
        "page_title": clean_text(post.get("title", "")),
        "page_description": clean_text(selftext)[:MAX_BODY_CHARS],
        "body_text": clean_text(selftext)[:MAX_BODY_CHARS],
        "outbound_links": markdown_links[:100],
        "source_tags": [
            clean_text(post.get("subreddit", "")),
            clean_text(post.get("link_flair_text", "")),
        ],
        "http_status": response.status_code,
    }


def parse_discourse_json(session: requests.Session, url: str) -> dict | None:
    parsed = urlparse(url)
    match = re.search(r"/t/(?:[^/]+/)?(\d+)(?:/|$)", parsed.path)
    if not match:
        return None
    topic_id = match.group(1)
    endpoint = f"{parsed.scheme}://{parsed.netloc}/t/{topic_id}.json"
    response = session.get(
        endpoint,
        timeout=TIMEOUT,
        headers={"Accept": "application/json"},
    )
    if response.status_code in {403, 404, 410, 429}:
        return {
            "retrieval_method": "discourse_json",
            "http_status": response.status_code,
            "retrieval_error": f"HTTP {response.status_code}",
        }
    response.raise_for_status()
    data = response.json()
    stream = data.get("post_stream", {})
    posts = stream.get("posts", []) if isinstance(stream, dict) else []
    first = posts[0] if posts and isinstance(posts[0], dict) else {}
    cooked = first.get("cooked", "")
    cooked_soup = BeautifulSoup(cooked, "html.parser")
    body = clean_text(cooked_soup.get_text(" ", strip=True))
    outbound_links = extract_links(cooked_soup, url)
    return {
        "retrieval_method": "discourse_json",
        "page_title": clean_text(data.get("title", "")),
        "page_description": clean_text(data.get("excerpt", "")),
        "body_text": body[:MAX_BODY_CHARS],
        "outbound_links": outbound_links,
        "source_tags": [clean_text(str(tag)) for tag in data.get("tags", []) if clean_text(str(tag))],
        "http_status": response.status_code,
    }


def parse_html(
    session: requests.Session,
    url: str,
    base_url_override: str | None = None,
    timeout: int = TIMEOUT,
) -> dict:
    response = session.get(url, timeout=timeout, headers={"Accept": "text/html"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    def meta_content(*selectors: str) -> str:
        for selector in selectors:
            node = soup.select_one(selector)
            if node:
                value = node.get("content") or node.get_text(" ", strip=True)
                if value:
                    return clean_text(value)
        return ""

    page_title = clean_text(
        (soup.title.get_text(" ", strip=True) if soup.title else "")
        or meta_content('meta[property="og:title"]')
    )
    description = meta_content(
        'meta[name="description"]',
        'meta[property="og:description"]',
        'meta[name="twitter:description"]',
    )
    keywords = meta_content('meta[name="keywords"]')

    for node in soup.select(
        "script, style, noscript, nav, footer, header, aside, "
        "[role=navigation], .comments, #comments"
    ):
        node.decompose()

    # Forum engines use different post containers. Prefer actual post content
    # over meta descriptions, which are often only short excerpts and omit
    # attachment/download links. Choose the richest plausible content node after
    # removing navigation, comments widgets, scripts, and page chrome.
    # The first post carries the topic's intent. Using the entire thread as
    # body text lets later replies' "looking for" or "ripped from" phrases
    # incorrectly override an original resource post. Select the first plausible
    # post body for classification, but collect links from the wider thread.
    primary_body_selectors = (
        '[itemprop="articleBody"]',
        # Invision pages can contain recommended-post snippets before the real
        # topic. Prefer the actual comment container over generic rich-text
        # snippets so classification sees the original post's wording.
        ".ipsComment_content",
        ".cPost_contentWrap",
        ".ipsType_richText",
        ".postbody",
        ".post_body",
        ".messageContent",
        ".message-content",
        ".message-body",
        ".bbWrapper",
        ".post-content",
        ".post_content",
        ".postarea",
        ".entry-content",
        ".article-content",
        ".deviation-full",
        ".post",
        # Invision Community may render the topic under this container even when
        # the individual post-body class names differ from known versions.
        # Keep it as a fallback after specific post-body selectors so replies
        # do not outrank a recognizable first-post body.
        "#ipsLayout_mainArea",
        ".ipsLayout_mainArea",
        "article",
        "main",
        "#content",
        "#main",
    )
    body_node = None
    body = ""
    body_selector_used = None
    primary_selector_matches = {}
    for selector in primary_body_selectors:
        try:
            nodes = soup.select(selector)
            primary_selector_matches[selector] = len(nodes)
        except Exception:
            primary_selector_matches[selector] = -1
            continue
        for node in nodes:
            text_value = clean_text(node.get_text(" ", strip=True))
            if len(text_value) >= 80:
                body_node = node
                body = text_value
                body_selector_used = selector
                break
        if body_node is not None:
            break

    # Search links across all recognized post containers. Many older forum
    # engines (notably Invision Community) do not place posts under #content,
    # #main, or .postarea. Selecting only the largest generic container can
    # therefore miss downloads in replies. Aggregate links from specific post
    # bodies first, then broader containers; deduplicate by URL. Classification
    # still uses only the first post body above.
    link_selectors = (
        ".ipsType_richText",
        ".cPost_contentWrap",
        ".ipsComment_content",
        ".postbody",
        ".post_body",
        ".messageContent",
        ".message-content",
        ".message-body",
        ".bbWrapper",
        ".post-content",
        ".post_content",
        ".postarea",
        ".entry-content",
        ".article-content",
        ".deviation-full",
        ".post",
        # Fallback for Invision pages whose posts are nested in the main layout
        # area but do not expose a recognized individual post container.
        "#ipsLayout_mainArea",
        ".ipsLayout_mainArea",
        "article",
        "main",
        "#content",
        "#main",
    )
    base_url = base_url_override or response.url
    outbound_links = []
    seen_link_urls = set()
    seen_nodes = set()
    for selector in link_selectors:
        try:
            nodes = soup.select(selector)
        except Exception:
            continue
        for node in nodes:
            if id(node) in seen_nodes:
                continue
            seen_nodes.add(id(node))
            for link in extract_links(node, base_url):
                target = link.get("url")
                if not target or target in seen_link_urls:
                    continue
                seen_link_urls.add(target)
                outbound_links.append(link)
                if len(outbound_links) >= 100:
                    break
            if len(outbound_links) >= 100:
                break
        if len(outbound_links) >= 100:
            break
    if not body:
        body = description

    # Keep compact parser diagnostics so a short metadata fallback can be
    # distinguished from a successfully extracted post body in later audits.
    div_classes = []
    seen_classes = set()
    for div in soup.select("div[class]"):
        for class_name in div.get("class") or []:
            if class_name not in seen_classes:
                seen_classes.add(class_name)
                div_classes.append(str(class_name)[:80])
                if len(div_classes) >= 30:
                    break
        if len(div_classes) >= 30:
            break
    div_ids = []
    seen_ids = set()
    for div in soup.select("div[id]"):
        value = str(div.get("id") or "")
        if value and value not in seen_ids:
            seen_ids.add(value)
            div_ids.append(value[:100])
            if len(div_ids) >= 20:
                break
    raw_html = response.text
    lower_html = raw_html.lower()
    html_diagnostics = {
        "html_chars": len(raw_html),
        "body_text_chars": len(body),
        "body_excerpt": body[:300],
        "body_node_found": body_node is not None,
        "body_source": body_selector_used or ("meta_description" if description else "empty"),
        "body_selector_used": body_selector_used,
        "matched_primary_selectors": {
            selector: count
            for selector, count in primary_selector_matches.items()
            if count != 0
        },
        "div_classes_sample": div_classes,
        "div_ids_sample": div_ids,
        "raw_script_tag_count": lower_html.count("<script"),
        "raw_has_article_body_key": "articlebody" in lower_html,
        "raw_has_invision_post_classes": any(
            marker in lower_html
            for marker in (
                "ipscomment_content",
                "ipstype_richtext",
                "cpost_contentwrap",
                "bbwrapper",
            )
        ),
        "raw_has_attachment_marker": "attachment" in lower_html,
        "raw_has_download_marker": "download" in lower_html,
    }

    return {
        "retrieval_method": "html",
        "html_diagnostics": html_diagnostics,
        "http_status": response.status_code,
        "final_url": response.url,
        "page_title": page_title,
        "page_description": description[:1600],
        "body_text": body[:MAX_BODY_CHARS],
        "outbound_links": outbound_links,
        "source_tags": [part.strip() for part in keywords.split(",") if part.strip()][:30],
    }


def invision_query_topic_url(url: str) -> str | None:
    """Build Invision's explicit topic-controller URL from a friendly topic URL."""
    match = re.search(r"/topic/(\d+)", url, re.I)
    parsed = urlparse(url)
    if not match or parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    query = urlencode({
        "app": "forums",
        "module": "forums",
        "controller": "topic",
        "id": match.group(1),
    })
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{query}"


def try_invision_query_fallback(
    session: requests.Session,
    original_url: str,
    original_page: dict,
) -> dict:
    """Retry an Invision topic through its explicit controller route when the
    friendly route returns only a short topic header and no post body.
    """
    host = (urlparse(original_url).hostname or "").lower()
    diagnostics = original_page.get("html_diagnostics") or {}
    body_source = diagnostics.get("body_source")
    body_chars = len(str(original_page.get("body_text") or ""))
    if (
        not host.endswith("rpg2s.it")
        or body_source not in {"#ipsLayout_mainArea", ".ipsLayout_mainArea", "meta_description", "empty"}
        or body_chars > 300
    ):
        return original_page

    alternate_url = invision_query_topic_url(original_url)
    if not alternate_url or alternate_url == original_url:
        return original_page

    try:
        alternate = parse_html(session, alternate_url)
    except requests.RequestException as exc:
        diagnostics.update({
            "alternate_route_attempted": True,
            "alternate_route_url": alternate_url,
            "alternate_route_error": type(exc).__name__,
            "alternate_route_used": False,
        })
        original_page["html_diagnostics"] = diagnostics
        return original_page

    alternate_diagnostics = alternate.get("html_diagnostics") or {}
    alternate_body_chars = len(str(alternate.get("body_text") or ""))
    original_link_count = len(original_page.get("outbound_links") or [])
    alternate_link_count = len(alternate.get("outbound_links") or [])
    alternate_source = alternate_diagnostics.get("body_source")
    specific_post_body = (
        alternate_source not in {
            "#ipsLayout_mainArea", ".ipsLayout_mainArea", "meta_description", "empty", None
        }
        and alternate_body_chars >= 80
    )
    materially_better = (
        alternate.get("http_status") == 200
        and (
            specific_post_body
            or alternate_body_chars >= body_chars + 150
            or alternate_link_count >= original_link_count + 3
        )
    )

    diagnostics.update({
        "alternate_route_attempted": True,
        "alternate_route_url": alternate_url,
        "alternate_route_http_status": alternate.get("http_status"),
        "alternate_route_body_source": alternate_source,
        "alternate_route_body_chars": alternate_body_chars,
        "alternate_route_link_count": alternate_link_count,
        "alternate_route_used": bool(materially_better),
    })
    if not materially_better:
        original_page["html_diagnostics"] = diagnostics
        return original_page

    alternate_diagnostics["alternate_route_attempted"] = True
    alternate_diagnostics["alternate_route_url"] = alternate_url
    alternate_diagnostics["alternate_route_body_source"] = alternate_source
    alternate_diagnostics["alternate_route_body_chars"] = alternate_body_chars
    alternate_diagnostics["alternate_route_link_count"] = alternate_link_count
    alternate_diagnostics["alternate_route_used"] = True
    alternate_diagnostics["fallback_from_url"] = original_url
    alternate["html_diagnostics"] = alternate_diagnostics
    alternate["retrieval_method"] = "html_invision_query_fallback"
    alternate["requested_url"] = original_url
    return alternate


def try_wayback_fallback(
    session: requests.Session,
    original_url: str,
    original_page: dict,
) -> dict:
    """Use a Wayback snapshot only when an Rpg2S page exposes a short topic
    header but no post body. Never treat an archive hit alone as a resource.
    """
    host = (urlparse(original_url).hostname or "").lower()
    diagnostics = original_page.get("html_diagnostics") or {}
    body_source = diagnostics.get("body_source")
    body_chars = len(str(original_page.get("body_text") or ""))
    if (
        not host.endswith("rpg2s.it")
        or body_source not in {"#ipsLayout_mainArea", ".ipsLayout_mainArea", "meta_description", "empty"}
        or body_chars > 300
    ):
        return original_page

    cdx_url = "https://web.archive.org/cdx/search/cdx"
    params = [
        ("url", original_url),
        ("output", "json"),
        ("fl", "timestamp,original,statuscode,mimetype"),
        ("filter", "statuscode:200"),
        ("filter", "mimetype:text/html"),
        ("collapse", "digest"),
    ]
    try:
        cdx_response = session.get(
            cdx_url,
            params=params,
            timeout=6,
            headers={"Accept": "application/json"},
        )
        cdx_response.raise_for_status()
        records = json.loads(cdx_response.text)
    except (requests.RequestException, ValueError, TypeError) as exc:
        diagnostics.update({
            "wayback_attempted": True,
            "wayback_snapshot_found": False,
            "wayback_error": type(exc).__name__,
        })
        original_page["html_diagnostics"] = diagnostics
        return original_page

    snapshots = [
        row for row in records[1:]
        if isinstance(row, list)
        and len(row) >= 4
        and row[2] == "200"
        and "html" in str(row[3]).lower()
        and re.fullmatch(r"\\d{8,14}", str(row[0]))
    ] if isinstance(records, list) and records else []

    if not snapshots:
        diagnostics.update({
            "wayback_attempted": True,
            "wayback_snapshot_found": False,
            "wayback_cdx_http_status": cdx_response.status_code,
            "wayback_error": "no_matching_snapshot",
        })
        original_page["html_diagnostics"] = diagnostics
        return original_page

    timestamp, snapshot_original, status_code, mime_type = snapshots[-1][:4]
    archive_url = f"https://web.archive.org/web/{timestamp}id_/{snapshot_original}"
    try:
        archived = parse_html(
            session,
            archive_url,
            base_url_override=original_url,
            timeout=6,
        )
    except requests.RequestException as exc:
        diagnostics.update({
            "wayback_attempted": True,
            "wayback_snapshot_found": True,
            "wayback_snapshot_timestamp": timestamp,
            "wayback_archive_url": archive_url,
            "wayback_error": type(exc).__name__,
            "wayback_used": False,
        })
        original_page["html_diagnostics"] = diagnostics
        return original_page

    archived_diagnostics = archived.get("html_diagnostics") or {}
    archived_body_chars = len(str(archived.get("body_text") or ""))
    original_link_count = len(original_page.get("outbound_links") or [])
    archived_link_count = len(archived.get("outbound_links") or [])
    archived_source = archived_diagnostics.get("body_source")
    specific_post_body = (
        archived_source not in {
            "#ipsLayout_mainArea", ".ipsLayout_mainArea", "meta_description", "empty", None
        }
        and archived_body_chars >= 80
    )
    materially_better = (
        archived.get("http_status") == 200
        and (
            specific_post_body
            or (
                archived_body_chars >= body_chars + 150
                and archived_link_count >= original_link_count + 1
            )
        )
    )

    diagnostics.update({
        "wayback_attempted": True,
        "wayback_snapshot_found": True,
        "wayback_cdx_http_status": cdx_response.status_code,
        "wayback_snapshot_timestamp": timestamp,
        "wayback_snapshot_original": snapshot_original,
        "wayback_archive_url": archive_url,
        "wayback_archive_http_status": archived.get("http_status"),
        "wayback_body_source": archived_source,
        "wayback_body_chars": archived_body_chars,
        "wayback_link_count": archived_link_count,
        "wayback_used": bool(materially_better),
    })
    if not materially_better:
        original_page["html_diagnostics"] = diagnostics
        return original_page

    archived_diagnostics.update({
        "wayback_attempted": True,
        "wayback_snapshot_found": True,
        "wayback_cdx_http_status": cdx_response.status_code,
        "wayback_snapshot_timestamp": timestamp,
        "wayback_snapshot_original": snapshot_original,
        "wayback_archive_url": archive_url,
        "wayback_archive_http_status": archived.get("http_status"),
        "wayback_body_source": archived_source,
        "wayback_body_chars": archived_body_chars,
        "wayback_link_count": archived_link_count,
        "wayback_used": True,
        "fallback_from_url": original_url,
    })
    archived["html_diagnostics"] = archived_diagnostics
    archived["retrieval_method"] = "wayback_archive_fallback"
    archived["requested_url"] = original_url
    return archived



def fetch_item(session: requests.Session, item: dict) -> dict:
    url = str(item.get("url") or "").strip()
    result = {
        "pre_id": item.get("pre_id"),
        "title": item.get("title"),
        "source": item.get("source"),
        "url": url,
        "historical_decision": item.get("decision"),
        "review_note": item.get("review_note"),
        "retrieval_status": "unavailable",
        "retrieval_method": "none",
        "page_title": "",
        "page_description": "",
        "body_text": "",
        "outbound_links": [],
        "source_tags": [],
        "http_status": None,
        "retrieval_error": "",
    }
    if not is_public_http_url(url):
        result["retrieval_error"] = "Invalid or non-public HTTP(S) URL"
        return result

    host = (urlparse(url).hostname or "").lower()
    try:
        if host.endswith("reddit.com"):
            page = parse_reddit_json(session, url)
        else:
            page = parse_discourse_json(session, url)
            if page is None:
                page = parse_html(session, url)
                page = try_invision_query_fallback(session, url, page)
                page = try_wayback_fallback(session, url, page)
        result.update(page)
        if result.get("body_text") or result.get("page_description"):
            result["retrieval_status"] = "body_found"
        elif result.get("http_status") == 200:
            result["retrieval_status"] = "page_loaded_no_body"
        else:
            result["retrieval_status"] = "unavailable"
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        result["http_status"] = status
        result["retrieval_error"] = f"HTTP {status}" if status else "HTTP error"
    except requests.RequestException as exc:
        result["retrieval_error"] = type(exc).__name__
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        result["retrieval_error"] = f"Parse error: {type(exc).__name__}"
    except Exception as exc:  # one broken site must not stop the audit
        result["retrieval_error"] = f"Unexpected error: {type(exc).__name__}"
    return result


def main() -> int:
    ledger_path = Path(sys.argv[1]) if len(sys.argv) > 1 else LEDGER_PATH
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else OUTPUT_PATH
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[Body audit] Cannot read ledger: {exc}", file=sys.stderr)
        return 2

    items = ledger.get("items", [])
    selected = [
        item for item in items
        if isinstance(item, dict)
        and item.get("pre_id", "").startswith("PRE-")
        and item.get("status") == "resolved"
        and item.get("decision") in {"confirmed", "not_applicable", "reviewed"}
        and int(item["pre_id"].split("-")[1]) <= MAX_ITEMS
    ]
    selected.sort(key=lambda item: int(item["pre_id"].split("-")[1]))

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    results = []
    total = len(selected)
    for index, item in enumerate(selected, start=1):
        record = fetch_item(session, item)
        results.append(record)
        print(
            f"[Body audit] {index}/{total} {record['pre_id']} "
            f"{record['retrieval_status']} {record.get('http_status') or ''}"
        )
        time.sleep(PAUSE_SECONDS)

    counts: dict[str, int] = {}
    for record in results:
        status = record["retrieval_status"]
        counts[status] = counts.get(status, 0) + 1

    output = {
        "schema_version": 1,
        "audit_only": True,
        "source_ledger": str(ledger_path),
        "requested_item_count": len(results),
        "retrieval_counts": dict(sorted(counts.items())),
        "note": (
            "Public page retrieval attempt only. Historical decisions are preserved; "
            "this output does not alter the review ledger or runtime classification. "
            "Unavailable pages are not treated as evidence for exclusion."
        ),
        "items": results,
    }
    output_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[Body audit] Wrote {output_path}; counts={counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
