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


def tracked_get(url, **kwargs):
    """Perform a GET request and record success/failure for the current collector."""
    allow_status_codes = set(kwargs.pop("allow_status_codes", ()))
    kwargs.setdefault("headers", HEADERS)
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    try:
        response = requests.get(url, **kwargs)
        if response.status_code in allow_status_codes:
            _REQUEST_STATS["failed"] += 1
            return response
        response.raise_for_status()
    except Exception:
        _REQUEST_STATS["failed"] += 1
        raise
    _REQUEST_STATS["succeeded"] += 1
    return response


def get_html(url):
    """Fetch a page and record transport/HTTP failures for source health."""
    return tracked_get(url).text


def get_feed(url):
    """Fetch a feed through the shared request layer, then parse its body."""
    import feedparser

    response = tracked_get(url)
    feed = feedparser.parse(response.content)
    if getattr(feed, "bozo", False):
        # A parse error with no entries means the request did not produce
        # usable feed data; count it as a failed collection attempt.
        if not getattr(feed, "entries", []):
            _REQUEST_STATS["succeeded"] = max(0, _REQUEST_STATS["succeeded"] - 1)
        _REQUEST_STATS["failed"] += 1
    return feed
