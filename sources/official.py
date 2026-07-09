import requests
from bs4 import BeautifulSoup

from config import (
    OFFICIAL_NEWS_URL,
    USER_AGENT,
    REQUEST_TIMEOUT,
)

def classify_official(title):

    title_lower = title.lower()

    if "unite" in title_lower:
        return "UNITE"

    if (
        "forum" in title_lower
        or "yanfly" in title_lower
        or "migration" in title_lower
        or "archive" in title_lower
    ):
        return "Forum重要事項"

    return "本体ニュース"


def get_official_news_items(seen):

    new_seen = seen.copy()
    adopted_items = []

    try:

        response = requests.get(
            OFFICIAL_NEWS_URL,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": USER_AGENT
            }
        )

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        for tag in soup.find_all("h3"):

            title = tag.get_text(strip=True)

            if not title:
                continue

            if title in seen:
                continue

            new_seen.append(title)

            adopted_items.append(
                {
                    "title": title,
                    "url": OFFICIAL_NEWS_URL,
                    "category": classify_official(title),
                }
            )

        print(
            "Official News new:",
            len(adopted_items)
        )

    except Exception as e:

        print(
            "Official News error:",
            str(e)
        )

    return adopted_items, new_seen
