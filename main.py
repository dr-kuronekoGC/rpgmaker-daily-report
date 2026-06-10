import feedparser

RSS_URL = "https://www.rpgmakerweb.com/all-posts"

feed = feedparser.parse(RSS_URL)

print("feed title:", feed.feed.get("title"))

print("取得件数:", len(feed.entries))

for entry in feed.entries[:5]:
    print(entry.title)
