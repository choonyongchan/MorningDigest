from types import SimpleNamespace

import pytest

import summariser as summariser_module
from commons import Article, Feed


class DummyResponses:
    def create(self, **_kwargs):
        return SimpleNamespace(output_text="Mock summary text")


class DummyClient:
    def __init__(self):
        self.responses = DummyResponses()


def test_feed_to_str_serialises_articles():
    feed = Feed(
        name="Sample Feed",
        tags=["sample"],
        url="https://example.com/feed",
        article=[
            Article(
                title="Story",
                url="https://example.com/story",
                summary="Brief",
                published="Mon, 01 Jan 2024 00:00:00 GMT",
            ),
            Article(
                title="Another",
                url="https://example.com/another",
                summary="Details",
                published="Mon, 01 Jan 2024 00:00:00 GMT",
            ),
        ],
    )

    text = summariser_module.Summariser.feed_to_str([feed])

    assert "Sample Feed: Story: Brief" in text
    assert "Sample Feed: Another: Details" in text


def test_summarise_sets_user_summary(monkeypatch, sample_user):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(summariser_module.Summariser, "CLIENT", DummyClient())

    summariser = summariser_module.Summariser(model="mock")
    summariser.invoke_model = lambda instructions, prompt: "Generated summary"  # type: ignore[assignment]

    summariser.summarise([sample_user])

    assert sample_user.summary == "Generated summary"


def test_check_api_key_missing(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(EnvironmentError):
        summariser_module.Summariser.check_api_key()
