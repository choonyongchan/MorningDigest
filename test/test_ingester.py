"""Tests for the ingester helpers."""

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

import ingester as ingester_module  # noqa: E402
from commons import Article  # noqa: E402


def test_format_article_trims_fields():
    entry = {
        "title": "  Morning Rush  ",
        "published": "Mon, 01 Jan 2024 08:00:00 GMT",
        "summary": "  Markets rally  ",
    }

    article = ingester_module.Ingester.format_article(entry)

    assert isinstance(article, Article)
    assert article.title == "Morning Rush"
    assert article.published == "Mon, 01 Jan 2024 08:00:00 GMT"
    assert article.summary == "Markets rally"


def test_fetch_feed_uses_feedparser(monkeypatch):
    sample_entries = [
        {"title": "Story", "published": "Mon, 01 Jan 2024 00:00:00 GMT", "summary": "Snippet"}
    ]

    def fake_parse(url):
        assert url == "https://example.com/feed"
        return SimpleNamespace(entries=sample_entries)

    monkeypatch.setattr(ingester_module.feedparser, "parse", fake_parse)

    articles = ingester_module.Ingester.fetch_feed("https://example.com/feed")

    assert len(articles) == 1
    assert articles[0].title == "Story"


def test_filter_today_articles_respects_allowed_dates(monkeypatch):
    allowed_dt = datetime(2024, 1, 2, 8, 0, tzinfo=timezone.utc)
    allowed_date = allowed_dt.date()
    monkeypatch.setattr(
        ingester_module.Ingester,
        "get_allowed_dates",
        staticmethod(lambda: {allowed_date}),
    )

    allowed_article = Article(
        title="Fresh",
        url="https://example.com/fresh",
        published=allowed_dt.strftime("%a, %d %b %Y %H:%M:%S GMT"),
        summary="Allowed",
    )
    old_article = Article(
        title="Stale",
        url="https://example.com/stale",
        published="Mon, 01 Jan 2024 08:00:00 GMT",
        summary="Ignore",
    )

    filtered = ingester_module.Ingester.filter_today_articles([allowed_article, old_article])

    assert [article.title for article in filtered] == ["Fresh"]


def test_match_feeds_returns_unique_matches():
    matches = ingester_module.Ingester.match_feeds(["StraitsTimes Tech", "business"])

    names = [feed.name for feed in matches]

    assert names == [
        "StraitsTimes Tech",
        "StraitsTimes Business",
        "ChannelNewsAsia Business",
    ]