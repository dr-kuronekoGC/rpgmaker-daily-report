import requests

from config import REQUEST_TIMEOUT

# Per-collector request diagnostics. Collectors run sequentially in main.py.
_REQUEST_STATS = {"succeeded": 0, "failed": 0}


def reset_request_stats():
    """Reset shared HTTP diagnostics before one collector runs."""
    _REQUEST_STATS["succeeded"] = 0
    _REQUEST_STATS["failed"] = 0


def get_request_stats():
    """Return a copy so callers cannot mutate the shared counters."""
    return dict(_REQUEST_STATS)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/138.0 Safari/537.36"
    )
}


def get_html(url):
    """Fetch a page and record transport/HTTP failures for source health."""
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except Exception:
        _REQUEST_STATS["failed"] += 1
        raise

    _REQUEST_STATS["succeeded"] += 1
    return response.text


def get_feed(url):
    """Fetch and parse a feed while exposing basic request health."""
    import feedparser

    try:
        feed = feedparser.parse(url)
    except Exception:
        _REQUEST_STATS["failed"] += 1
        raise

    status = getattr(feed, "status", None)
    bozo = bool(getattr(feed, "bozo", False))
    entries = getattr(feed, "entries", [])
    if (isinstance(status, int) and status >= 400) or (bozo and not entries):
        _REQUEST_STATS["failed"] += 1
    else:
        _REQUEST_STATS["succeeded"] += 1
    return feed
