import requests
from bs4 import BeautifulSoup

from config import (
    OFFICIAL_NEWS_URL,
    USER_AGENT,
    REQUEST_TIMEOUT,
)


# ==========================================
# Category
# ==========================================

CATEGORY_KEYWORDS = {
    "UNITE": [
        "unite",
    ],

    "Forum重要事項": [
        "forum",
        "yanfly",
        "migration",
        "archive",
    ],
}


def classify(title):

    title_lower = title.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():

        for keyword in keywords:

            if keyword in title_lower:
                return category

    return "本体ニュース"


# ==========================================
# Official News
# ==========================================

def get_official_news_items(seen):

    adopted_items = []

    new_seen = seen.copy()

    try:

        response = requests.get(
            OFFICIAL_NEWS_URL,
            headers={
                "User-Agent": USER_AGENT
            },
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        for tag in soup.find_all("h3"):

            title = tag.get_text(strip=True)

            if not title:
                continue

            if title in seen:
                continue

            new_seen.append(title)

            category = classify(title)

            adopted_items.append(
                {
                    "title": title,
                    "url": OFFICIAL_NEWS_URL,
                    "category": category,
                }
            )

            print(
                f"[Official][{category}] {title}"
            )

    except Exception as e:

        print(
            "Official News error:",
            e,
        )

    print(
        "Official News new:",
        len(adopted_items),
    )

    return adopted_items, new_seen
