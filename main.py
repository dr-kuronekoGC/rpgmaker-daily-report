import feedparser

RSS_URL = "https://www.rpgmakerweb.com/blog/rss.xml"

feed = feedparser.parse(RSS_URL)

print("取得件数:", len(feed.entries))

for entry in feed.entries[:5]:
    print(entry.title)
