import feedparser

RSS_URL = "https://www.reddit.com/r/RPGMaker/.rss"

feed = feedparser.parse(RSS_URL)

print("feed title:", feed.feed.get("title"))
print("entries:", len(feed.entries))

print("\n--- 最新5件 ---")

for entry in feed.entries[:5]:
    print(entry.title)
    print(entry.link)
    print()
