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
from urllib.parse import urljoin, urlparse

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
            r"/(?:themes?/|avatars?/|ranks?/|medals?/|images/post/|smilies/|emoticons?/|users?/avatar)",
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

    # Older forum posts sometimes embed asset images directly without anchors.
    # Capture them as evidence, while downstream checks still require semantic
    # attachment filenames to distinguish assets from random previews.
    for image_node in node.select("img[src]"):
        href = urljoin(base_url, str(image_node.get("src") or "").strip())
        parsed = urlparse(href)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or href in seen:
            continue
        if re.search(
            r"/(?:themes?/|avatars?/|ranks?/|medals?/|images/post/|smilies/|emoticons?/|users?/avatar)",
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


def parse_html(session: requests.Session, url: str) -> dict:
    response = session.get(url, timeout=TIMEOUT, headers={"Accept": "text/html"})
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
        "article",
        "main",
        "#content",
        "#main",
    )
    body_node = None
    body = ""
    for selector in primary_body_selectors:
        try:
            nodes = soup.select(selector)
        except Exception:
            continue
        for node in nodes:
            text_value = clean_text(node.get_text(" ", strip=True))
            if len(text_value) >= 80:
                body_node = node
                body = text_value
                break
        if body_node is not None:
            break

    # Search the broader thread for downloads and embedded images, but do not
    # feed reply text into intent classification.
    link_selectors = ("#content", "#main", "main", "article", ".postarea", ".post")
    link_candidates = []
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
            text_value = clean_text(node.get_text(" ", strip=True))
            if len(text_value) >= 80:
                link_candidates.append((len(text_value), node))
    link_node = max(link_candidates, key=lambda item: item[0])[1] if link_candidates else body_node
    outbound_links = extract_links(link_node, response.url)
    if not body:
        body = description

    return {
        "retrieval_method": "html",
        "http_status": response.status_code,
        "final_url": response.url,
        "page_title": page_title,
        "page_description": description[:1600],
        "body_text": body[:MAX_BODY_CHARS],
        "outbound_links": outbound_links,
        "source_tags": [part.strip() for part in keywords.split(",") if part.strip()][:30],
    }


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
