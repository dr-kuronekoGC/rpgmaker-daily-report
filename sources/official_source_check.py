import hashlib
import re
import requests
from bs4 import BeautifulSoup

from config import (
    REQUEST_TIMEOUT,
    SOURCE_CHECK_SEEN_FILE,
    SOURCE_CHECK_SITES,
)
from sources.base import HEADERS

SEEN_FILE = SOURCE_CHECK_SEEN_FILE
SOURCE_NAME = "Source Check"

# main.py reads this after get_items() to distinguish a complete scan
# from a scan where one or more monitored sites could not be checked.
LAST_RUN_SUMMARY = {
    "checked": 0,
    "updated": 0,
    "baseline": 0,
    "failed": 0,
    "unchanged": 0,
}

# Standard HTTP metadata fallback for sites whose page body may be inaccessible.
# This does not bypass access controls; it only uses ordinary HEAD responses.
HEADER_CHECK_FALLBACK_SITES = {
    "GameDevMarket",
    "Maker Devs",
    "RPG Refuge（2D素材フォーラム）",
}


class AccessChallengeError(ValueError):
    """The server returned an access challenge instead of the requested page."""

def normalize_url(url):
    if not isinstance(url, str):
        return None

    url = url.strip()

    if not url:
        return None

    return url.split("#", 1)[0]


def get_page(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    html = response.text

    # Some hosts return an HTTP 200 challenge page instead of the requested
    # content. Never store such a page as a valid baseline or page change.
    lowered = html[:20000].lower()
    challenge_markers = (
        "checking your browser",
        "/.stile/challenge",
        "cf-chl-",
        "verify you are human",
    )
    if any(marker in lowered for marker in challenge_markers):
        raise AccessChallengeError(
            "Access challenge page returned instead of monitored content"
        )

    return html


def get_rss_signature(url, base_url):
    """Build a signature from a publicly exposed RSS/Atom feed.

    This is an alternate public endpoint, not an attempt to bypass a challenge
    page. Challenge responses are rejected just as they are for normal pages.
    """
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    content = response.text
    lowered = content[:20000].lower()

    challenge_markers = (
        "checking your browser",
        "/.stile/challenge",
        "cf-chl-",
        "verify you are human",
    )
    if any(marker in lowered for marker in challenge_markers):
        raise AccessChallengeError(
            "Access challenge page returned instead of RSS content"
        )

    if not any(marker in lowered for marker in ("<rss", "<feed", "<rdf:rdf")):
        raise ValueError("Alternate endpoint did not return RSS/Atom XML")

    return build_signature(content, base_url)


def get_header_signature(url):
    """Build a change signature from standard HTTP metadata only.

    Requires ETag or Last-Modified. Content-Length alone is not reliable
    enough to claim that a page's contents have or have not changed.
    """
    response = requests.head(
        url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
        allow_redirects=True,
    )
    response.raise_for_status()

    etag = response.headers.get("ETag")
    last_modified = response.headers.get("Last-Modified")

    if not etag and not last_modified:
        raise ValueError(
            "HEAD response has no ETag or Last-Modified header"
        )

    metadata = "\n".join([
        response.url,
        etag or "",
        last_modified or "",
        response.headers.get("Content-Length", ""),
    ])

    return hashlib.sha256(
        metadata.encode("utf-8")
    ).hexdigest()


def build_signature(html, base_url):
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
        ]
    ):
        tag.decompose()

    links = []

    for link in soup.select("a[href]"):
        href = link.get("href")
        title = link.get_text(
            " ",
            strip=True,
        )

        if not href or not title:
            continue

        href = normalize_url(href)

        if href is None:
            continue

        if href.startswith("/"):
            from urllib.parse import urljoin

            href = urljoin(
                base_url,
                href,
            )

        # ナビゲーションやログイン系を除き、
        # 実際のコンテンツ候補だけを残す。
        text = re.sub(
            r"\s+",
            " ",
            title,
        ).strip()

        if len(text) < 3:
            continue

        if any(
            word in text.lower()
            for word in (
                "login",
                "log in",
                "subscribe",
                "sign up",
                "privacy",
                "cookie",
            )
        ):
            continue

        links.append(
            f"{text}|{href}"
        )

    links = sorted(set(links))

    # リンクがほとんどないサイトでも、
    # 本文変更をある程度検知できるように
    # ページ本文の先頭部分も含める。
    text = soup.get_text(
        " ",
        strip=True,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    signature_text = (
        "\n".join(links)
        + "\n"
        + text[:20000]
    )

    return hashlib.sha256(
        signature_text.encode(
            "utf-8"
        )
    ).hexdigest()


def get_items(seen):
    global LAST_RUN_SUMMARY

    if not isinstance(seen, dict):
        seen = {}

    new_seen = dict(seen)
    adopted_items = []
    summary = {
        "checked": 0,
        "updated": 0,
        "baseline": 0,
        "failed": 0,
        "unchanged": 0,
    }

    for site in SOURCE_CHECK_SITES:
        name = site["name"]
        url = site["url"]

        try:
            method = "page"
            try:
                html = get_page(url)
                signature = build_signature(
                    html,
                    url,
                )
            except Exception as page_error:
                alternate_feed_url = site.get("alternate_feed_url")

                if alternate_feed_url:
                    try:
                        signature = get_rss_signature(
                            alternate_feed_url,
                            url,
                        )
                        method = "rss"
                        print(
                            f"[{SOURCE_NAME}] "
                            f"RSS fallback OK: {name}"
                        )
                    except Exception as rss_error:
                        # Do not use header metadata after an access challenge.
                        if isinstance(page_error, AccessChallengeError):
                            raise ValueError(
                                f"Page check failed ({page_error}); "
                                f"RSS fallback failed ({rss_error})"
                            ) from rss_error

                        if name not in HEADER_CHECK_FALLBACK_SITES:
                            raise ValueError(
                                f"Page check failed ({page_error}); "
                                f"RSS fallback failed ({rss_error})"
                            ) from rss_error

                        try:
                            signature = get_header_signature(url)
                            method = "headers"
                            print(
                                f"[{SOURCE_NAME}] "
                                f"Header-only fallback OK: {name}"
                            )
                        except Exception as header_error:
                            raise ValueError(
                                f"Page check failed ({page_error}); "
                                f"RSS fallback failed ({rss_error}); "
                                f"header fallback failed ({header_error})"
                            ) from header_error
                elif isinstance(page_error, AccessChallengeError):
                    # Never treat challenge-page metadata as target-page metadata.
                    raise
                elif name in HEADER_CHECK_FALLBACK_SITES:
                    try:
                        signature = get_header_signature(url)
                        method = "headers"
                        print(
                            f"[{SOURCE_NAME}] "
                            f"Header-only fallback OK: {name}"
                        )
                    except Exception as header_error:
                        raise ValueError(
                            f"Page check failed ({page_error}); "
                            f"header fallback failed ({header_error})"
                        ) from header_error
                else:
                    raise

            summary["checked"] += 1
            previous = seen.get(name)

            # Page-body and header-only signatures are not comparable.
            previous_method = previous.get("method", "page") if previous else None
            if previous is None or previous_method != method:
                new_seen[name] = {
                    "url": url,
                    "signature": signature,
                    "method": method,
                }
                summary["baseline"] += 1
                print(
                    f"[{SOURCE_NAME}] "
                    f"Baseline: {name} ({method})"
                )
                continue

            if previous.get("signature") == signature:
                summary["unchanged"] += 1
                continue

            new_seen[name] = {
                "url": url,
                "signature": signature,
                "method": method,
            }
            summary["updated"] += 1

            adopted_items.append(
                {
                    "title": f"{name}：ページ変化あり（要確認）",
                    "url": url,
                    "category": "SourceCheck",
                    "source": SOURCE_NAME,
                    "resource_types": site.get("resource_types", []),
                    "language": site.get("language"),
                    "site_type": site.get("site_type"),
                }
            )

            print(
                f"[{SOURCE_NAME}] "
                f"Update: {name}"
            )

        except Exception as e:
            # Failed sites do not update their stored signatures.
            summary["failed"] += 1
            print(
                f"[{SOURCE_NAME}] "
                f"Skip: {name}: {e}"
            )

    LAST_RUN_SUMMARY = summary
    print(
        f"[{SOURCE_NAME}] Summary: "
        f"checked={summary['checked']}/{len(SOURCE_CHECK_SITES)} / "
        f"updated={summary['updated']} / "
        f"baseline={summary['baseline']} / "
        f"unchanged={summary['unchanged']} / "
        f"failed={summary['failed']}"
    )

    return adopted_items, new_seen
