import requests

from config import (
    USER_AGENT,
    REQUEST_TIMEOUT,
)


def get_html(url):

    response = requests.get(
        url,
        headers={
            "User-Agent": USER_AGENT,
        },
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    return response.text


def get_feed(url):
    import feedparser

    return feedparser.parse(url)
