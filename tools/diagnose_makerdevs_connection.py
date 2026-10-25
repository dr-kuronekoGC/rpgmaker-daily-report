"""Diagnostic-only connectivity checks for sites paused in Source Check.

Uses ordinary DNS, TCP, certificate-verified TLS, GET, and HEAD requests.
It does not bypass access controls or modify collection/state files.
"""
import socket
import ssl
from urllib.parse import urlparse

import requests

TARGETS = {
    "Maker Devs page": "https://makerdevs.com/mz/master-list",
    "RPG Refuge 2D Assets page": "https://rpg-refuge.com/forums/2d-assets.57/",
    "RPG Refuge 2D Assets RSS": "https://rpg-refuge.com/forums/2d-assets.57/index.rss",
}
TIMEOUT = (8, 12)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0 Safari/537.36"
    )
}


def diagnose_host(url):
    parsed = urlparse(url)
    hostname = parsed.hostname
    port = parsed.port or 443
    print(f"\n[host] {hostname}:{port}")

    try:
        records = socket.getaddrinfo(
            hostname, port, type=socket.SOCK_STREAM
        )
    except Exception as exc:
        print(f"[DNS] FAILED {type(exc).__name__}: {exc}")
        return

    addresses = []
    for family, socktype, proto, _, sockaddr in records:
        entry = (family, socktype, proto, sockaddr)
        if sockaddr[0] not in [item[3][0] for item in addresses]:
            addresses.append(entry)

    print("[DNS] " + (
        ", ".join(item[3][0] for item in addresses)
        if addresses else "no addresses"
    ))

    context = ssl.create_default_context()
    for family, socktype, proto, sockaddr in addresses[:4]:
        ip = sockaddr[0]
        stage = "TCP"
        try:
            with socket.socket(family, socktype, proto) as sock:
                sock.settimeout(5)
                sock.connect(sockaddr)
                stage = "TLS"
                with context.wrap_socket(
                    sock, server_hostname=hostname
                ) as tls_sock:
                    print(
                        f"[TLS] OK ip={ip} version={tls_sock.version()} "
                        f"cipher={tls_sock.cipher()[0]}"
                    )
        except Exception as exc:
            print(f"[{stage}] FAILED ip={ip} "
                  f"{type(exc).__name__}: {exc}")


def diagnose_url(label, url):
    print(f"\n[target] {label}: {url}")
    for method in ("GET", "HEAD"):
        try:
            response = requests.request(
                method,
                url,
                headers=HEADERS,
                timeout=TIMEOUT,
                allow_redirects=True,
            )
            content_type = response.headers.get("Content-Type", "")
            preview = response.text[:300].replace("\\n", " ") if method == "GET" else ""
            challenge = any(
                marker in preview.lower()
                for marker in (
                    "checking your browser",
                    "/.stile/challenge",
                    "cf-chl-",
                    "verify you are human",
                )
            )
            print(
                f"[HTTP {method}] status={response.status_code} "
                f"final_url={response.url!r} "
                f"content_type={content_type!r} "
                f"server={response.headers.get('Server', '')!r} "
                f"etag={response.headers.get('ETag', '')!r} "
                f"last_modified={response.headers.get('Last-Modified', '')!r}"
                + (f" challenge_marker={challenge}" if method == "GET" else "")
                + (f" preview={preview[:180]!r}" if method == "GET" else "")
            )
            response.close()
        except Exception as exc:
            print(f"[HTTP {method}] FAILED {type(exc).__name__}: {exc}")


def main():
    print(f"[diagnostic] python_ssl={ssl.OPENSSL_VERSION}")
    hosts = {}
    for url in TARGETS.values():
        parsed = urlparse(url)
        hosts.setdefault(parsed.hostname, url)
    for url in hosts.values():
        diagnose_host(url)
    for label, url in TARGETS.items():
        diagnose_url(label, url)
    print("\n[diagnostic] finished; no repository state was changed")


if __name__ == "__main__":
    main()
