from datetime import datetime, timezone
from types import SimpleNamespace

import organiser as organiser_module
from organiser import Headline, Organiser


class DummyQuoteResponse:
    def __init__(self, text: str = "Sail towards the sunrise.", author: str = "Test Author") -> None:
        self._payload = [{"q": text, "a": author}]

    def raise_for_status(self) -> None:  # pragma: no cover - no failure path in tests
        return None

    def json(self):
        return self._payload


def test_headlines_html_formats_items():
    now = datetime(2024, 1, 1, 8, 0, tzinfo=timezone.utc)
    headline = Headline(
        title="Markets rally",
        summary="Stocks inch higher on optimism.",
        feed_name="Sample Feed",
        published_at=now,
    )

    html = Organiser.build_headlines([headline])

    assert "Markets rally" in html
    assert "Sample Feed" not in html  # Feed name not shown in current implementation
    assert "<li>" in html


def test_build_creates_digest(tmp_path, monkeypatch, sample_user):
    def fake_get(*_args, **_kwargs):
        return DummyQuoteResponse()

    monkeypatch.setattr(organiser_module.requests, "get", fake_get)

    output_file = tmp_path / "digest.md"
    Organiser.build(user=sample_user, output_file=str(output_file))

    rendered = output_file.read_text(encoding="utf-8")
    assert sample_user.name in rendered
    assert "Sample personalised summary." in rendered
    assert "Sample Story" in rendered
