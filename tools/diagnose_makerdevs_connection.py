"""One-off network diagnostics for Maker Devs from GitHub Actions.

This script is diagnostic only. It does not disable TLS certificate validation,
change production monitoring, or modify any seen/state files.
"""
import socket
import ssl
from urllib.parse import urlparse

import requests

URL = "https://makerdevs.com/mz/master-list"
TIMEOUT = (8, 12)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0 Safari/537.36"
    )
}


def main():
    parsed = urlparse(URL)
    hostname = parsed.hostname
    port = parsed.port or 443
    print(f"[diagnostic] target={URL}")
    print(f"[diagnostic] python_ssl={ssl.OPENSSL_VERSION}")

    try:
        records = socket.getaddrinfo(
            hostname, port, type=socket.SOCK_STREAM
        )
    except Exception as exc:
        print(f"[DNS] FAILED {type(exc).__name__}: {exc}")
        records = []

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

    for method in ("GET", "HEAD"):
        try:
            response = requests.request(
                method,
                URL,
                headers=HEADERS,
                timeout=TIMEOUT,
                allow_redirects=True,
            )
            print(
                f"[HTTP {method}] status={response.status_code} "
                f"final_url={response.url!r} "
                f"server={response.headers.get('Server', '')!r} "
                f"via={response.headers.get('Via', '')!r} "
                f"etag={response.headers.get('ETag', '')!r} "
                f"last_modified={response.headers.get('Last-Modified', '')!r}"
            )
            response.close()
        except Exception as exc:
            print(f"[HTTP {method}] FAILED {type(exc).__name__}: {exc}")

    print("[diagnostic] finished; no repository state was changed")


if __name__ == "__main__":
    main()
