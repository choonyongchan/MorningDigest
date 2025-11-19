from typing import Any, List, Sequence, Set
import feedparser

from commons import Article, Feed
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

FEEDS: List[Feed] = [
    Feed(
        name="StraitsTimes World",
        tags=["straitstimes", "world", "international"],
        url="https://www.straitstimes.com/news/world/rss.xml",
    ),
    Feed(
        name="StraitsTimes Business",
        tags=["straitstimes", "business", "economy"],
        url="https://www.straitstimes.com/news/business/rss.xml",
    ),
    Feed(
        name="StraitsTimes Sport",
        tags=["straitstimes", "sport"],
        url="https://www.straitstimes.com/news/sport/rss.xml",
    ),
    Feed(
        name="StraitsTimes Life",
        tags=["straitstimes", "lifestyle"],
        url="https://www.straitstimes.com/news/life/rss.xml",
    ),
    Feed(
        name="StraitsTimes Opinion",
        tags=["straitstimes", "opinion"],
        url="https://www.straitstimes.com/news/opinion/rss.xml",
    ),
    Feed(
        name="StraitsTimes Singapore",
        tags=["straitstimes", "singapore"],
        url="https://www.straitstimes.com/news/singapore/rss.xml",
    ),
    Feed(
        name="StraitsTimes Asia",
        tags=["straitstimes", "asia"],
        url="https://www.straitstimes.com/news/asia/rss.xml",
    ),
    Feed(
        name="StraitsTimes Tech",
        tags=["straitstimes", "tech"],
        url="https://www.straitstimes.com/news/tech/rss.xml",
    ),
    Feed(
        name="StraitsTimes Multimedia",
        tags=["straitstimes", "multimedia"],
        url="https://www.straitstimes.com/news/multimedia/rss.xml",
    ),
    Feed(
        name="StraitsTimes Newsletter",
        tags=["straitstimes", "newsletter"],
        url="https://www.straitstimes.com/news/newsletter/rss.xml",
    ),
    Feed(
        name="ChannelNewsAsia Latest",
        tags=["channelnewsasia", "latest"],
        url="https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml",
    ),
    Feed(
        name="ChannelNewsAsia Asia",
        tags=["channelnewsasia", "asia"],
        url="https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6511",
    ),
    Feed(
        name="ChannelNewsAsia Business",
        tags=["channelnewsasia", "business"],
        url="https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6936",
    ),
    Feed(
        name="ChannelNewsAsia Singapore",
        tags=["channelnewsasia", "singapore"],
        url="https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=10416",
    ),
    Feed(
        name="ChannelNewsAsia Sport",
        tags=["channelnewsasia", "sport"],
        url="https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=10296",
    ),
    Feed(
        name="ChannelNewsAsia World",
        tags=["channelnewsasia", "world"],
        url="https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6311",
    ),
    Feed(
        name="ChannelNewsAsia Today",
        tags=["channelnewsasia", "today"],
        url="https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=679471",
    ),
    # Add other agencies below using the same structure.
]


class Ingester:

    @staticmethod
    def get_allowed_dates() -> Set[datetime.date]:
        now = datetime.now(timezone.utc)
        return {now.date(), (now - timedelta(days=1)).date()}

    @staticmethod
    def format_article(entry: Any) -> str:
        title = (entry.get("title") or "").strip()
        url = (entry.get("link") or "").strip()
        published = entry.get("published") or entry.get("updated") or ""
        summary = (entry.get("summary") or entry.get("description") or "").strip()
        return Article(
            title=title,
            url=url,
            published=published,
            summary=summary
        )

    @staticmethod
    def fetch_feed(url: str) -> Sequence[Article]:
        parsed = feedparser.parse(url)
        articles: List[Article] = [Ingester.format_article(entry) for entry in parsed.entries]
        return articles


    @staticmethod
    def filter_today_articles(articles: Sequence[Article]) -> Sequence[Article]:
        allowed_dates = Ingester.get_allowed_dates()

        filtered: List[Article] = []
        for article in articles:
            published = article.published
            if not published:
                raise ValueError("Article has no published date")
            parsed = parsedate_to_datetime(published)
            if parsed is None:
                raise ValueError("Failed to parse published date")
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            if parsed.astimezone(timezone.utc).date() in allowed_dates:
                filtered.append(article)

        return filtered

    @staticmethod
    def populate_feeds() -> None:
        for feed in FEEDS:
            # Logic to fetch and populate feed.result
            articles: Sequence[Article] = Ingester.fetch_feed(feed.url)
            today_articles: Sequence[Article] = Ingester.filter_today_articles(articles)
            feed.article = today_articles

    @staticmethod
    def match_feeds(selected_feeds: Sequence[str]) -> Sequence[Feed]:
        matched: dict[str, Feed] = {}
        for keyword in selected_feeds:
            for feed in FEEDS:
                if keyword == feed.name or keyword in feed.tags:
                    matched[feed.name] = feed
        return list(matched.values())