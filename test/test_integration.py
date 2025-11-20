from pathlib import Path
from types import SimpleNamespace

import organiser as organiser_module
import summariser as summariser_module
from commons import Article, Feed, User


class DummyQuoteResponse:
    def raise_for_status(self):  # pragma: no cover - no network in tests
        return None

    def json(self):
        return [{"q": "Stay curious.", "a": "Integration Bot"}]


class DummyClient:
    def __init__(self):
        self.responses = SimpleNamespace(create=lambda **_kwargs: SimpleNamespace(output_text="Integrated summary"))


def test_summary_to_digest_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "integration-key")
    monkeypatch.setattr(summariser_module.Summariser, "CLIENT", DummyClient())

    feed = Feed(
        name="Integration Feed",
        tags=["integration"],
        url="https://example.com/feed",
        article=[
            Article(
                title="Integration story",
                url="https://example.com/integration/story",
                summary="Integration details",
                published="Mon, 01 Jan 2024 00:00:00 GMT",
            )
        ],
    )
    user = User(username="integration", name="Integration User", selected_feeds=[feed])

    summariser = summariser_module.Summariser(model="mock")
    summariser.invoke_model = lambda instructions, prompt: "Integrated summary"  # type: ignore[assignment]
    summariser.summarise([user])
    user.top_articles = feed.article

    def fake_get(*_args, **_kwargs):
        return DummyQuoteResponse()

    monkeypatch.setattr(organiser_module.requests, "get", fake_get)

    output_path = tmp_path / "integration.md"
    organiser_module.Organiser.build(user=user, output_file=str(output_path))

    content = output_path.read_text(encoding="utf-8")
    assert "Integrated summary" in content
    assert "Integration User" in content
    assert "Integration story" in content
