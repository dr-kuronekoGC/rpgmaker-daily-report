import feedparser

RSS_URL = "https://www.reddit.com/r/RPGMaker/.rss"

feed = feedparser.parse(RSS_URL)

print("status:", getattr(feed, "status", "none"))
print("bozo:", feed.bozo)

if feed.bozo:
    print("error:", feed.bozo_exception)

print("feed title:", feed.feed.get("title"))
print("entries:", len(feed.entries))
