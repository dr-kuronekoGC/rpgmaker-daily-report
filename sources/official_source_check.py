import hashlib
import re
import requests
from bs4 import BeautifulSoup

from config import (
    REQUEST_TIMEOUT,
    SOURCE_CHECK_SEEN_FILE,
    SOURCE_CHECK_SITES,
    USER_AGENT,
)

SEEN_FILE = SOURCE_CHECK_SEEN_FILE
SOURCE_NAME = "Source Check"

HEADERS = {
    "User-Agent": USER_AGENT,
}


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
    return response.text


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
    if not isinstance(seen, dict):
        seen = {}

    new_seen = dict(seen)
    adopted_items = []

    for site in SOURCE_CHECK_SITES:
        name = site["name"]
        url = site["url"]

        try:
            html = get_page(url)
            signature = build_signature(
                html,
                url,
            )

            previous = seen.get(name)

            if previous is None:
                new_seen[name] = {
                    "url": url,
                    "signature": signature,
                }
                print(
                    f"[{SOURCE_NAME}] "
                    f"Baseline: {name}"
                )
                continue

            if previous.get("signature") == signature:
                continue

            new_seen[name] = {
                "url": url,
                "signature": signature,
            }

            adopted_items.append(
                {
                    "title": f"{name}：更新あり",
                    "url": url,
                    "category": "SourceCheck",
                    "source": SOURCE_NAME,
                }
            )

            print(
                f"[{SOURCE_NAME}] "
                f"Update: {name}"
            )

        except Exception as e:
            print(
                f"[{SOURCE_NAME}] "
                f"Skip: {name}: {e}"
            )

    return adopted_items, new_seen
