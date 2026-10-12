# ==========================================
# Maker Devs
# ==========================================

import requests
import socket
import ssl

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import (
    MAKER_DEVS_URL,
    MAKER_DEVS_SEEN_FILE,
)
from sources.base import get_html

SEEN_FILE = MAKER_DEVS_SEEN_FILE


def log_tls_diagnostics(url):
    """
    Log DNS and verified TLS-handshake details after an HTTPS SSL error.
    This is diagnostic only: it never disables certificate verification
    and never changes the collector's success/failure result.
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    hostname = parsed.hostname
    port = parsed.port or 443

    if not hostname:
        print("[Maker Devs Diagnostics] URL has no hostname.")
        return

    try:
        addresses = socket.getaddrinfo(
            hostname,
            port,
            type=socket.SOCK_STREAM,
        )
    except Exception as e:
        print(
            "[Maker Devs Diagnostics] DNS failed: "
            f"{type(e).__name__}: {e}"
        )
        return

    unique_addresses = []
    seen_addresses = set()
    for family, socktype, proto, _, sockaddr in addresses:
        address = sockaddr[0]
        key = (family, address)
        if key not in seen_addresses:
            seen_addresses.add(key)
            unique_addresses.append(
                (family, socktype, proto, sockaddr)
            )

    print(
        "[Maker Devs Diagnostics] DNS: "
        + ", ".join(address[3][0] for address in unique_addresses)
    )

    context = ssl.create_default_context()
    for family, socktype, proto, sockaddr in unique_addresses[:2]:
        address = sockaddr[0]
        stage = "TCP connect"
        try:
            with socket.socket(family, socktype, proto) as raw_socket:
                raw_socket.settimeout(5)
                raw_socket.connect(sockaddr)
                stage = "TLS handshake"
                with context.wrap_socket(
                    raw_socket,
                    server_hostname=hostname,
                ) as tls_socket:
                    print(
                        "[Maker Devs Diagnostics] TLS OK: "
                        f"ip={address} / "
                        f"version={tls_socket.version()}"
                    )
        except Exception as e:
            print(
                "[Maker Devs Diagnostics] "
                f"{stage} failed for {address}: "
                f"{type(e).__name__}: {e}"
            )


# ==========================================
# Plugin分類
# ==========================================

def classify_makerdevs(title, url=""):

    normalized = title.lower().strip()

    if normalized:
        return "RPG Makerプラグイン"

    return None


# ==========================================
# Main
# ==========================================

def get_items(seen):

    try:

        # 他のHTML収集元と同じ共通HTTP設定を使う。
        # 個別User-Agentとtimeoutの違いがTLSエラーに
        # 影響しているかを切り分けるための低リスクな検証。
        html = get_html(MAKER_DEVS_URL)

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        adopted_items = []
        new_seen = seen.copy()

        seen_urls = set()

        for link in soup.select("a[href]"):

            href = link.get("href")

            if not href:
                continue

            href = urljoin(
                MAKER_DEVS_URL,
                href,
            )

            if "makerdevs.com/" not in href:
                continue

            if (
                href.rstrip("/")
                == MAKER_DEVS_URL.rstrip("/")
            ):
                continue

            if href in seen_urls:
                continue

            seen_urls.add(href)

            if href in seen:
                continue

            title = link.get_text(
                " ",
                strip=True,
            )

            if not title:
                continue

            excluded_titles = {
                "home",
                "about",
                "contact",
                "login",
                "register",
                "search",
                "next",
                "previous",
                "back",
            }

            if title.lower() in excluded_titles:
                continue

            category = classify_makerdevs(
                title,
                href,
            )

            if category is None:
                continue

            new_seen.append(href)

            adopted_items.append(
                {
                    "title": title,
                    "url": href,
                    "category": category,
                    "source": "Maker Devs",
                }
            )

        print(
            f"[Maker Devs] New: "
            f"{len(adopted_items)}"
        )

        return (
            adopted_items,
            new_seen,
        )

    except requests.exceptions.SSLError as e:

        print(
            f"[Maker Devs] SSL Error: {e}"
        )
        log_tls_diagnostics(MAKER_DEVS_URL)

        raise

    except requests.exceptions.RequestException as e:

        print(
            f"[Maker Devs] Request Error: {e}"
        )

        raise

    except Exception as e:

        print(
            f"[Maker Devs] Error: {e}"
        )

        raise
