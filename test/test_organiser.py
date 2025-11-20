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
    headline = Headline(title="Markets rally", url="https://example.com/markets-rally")

    html = Organiser.build_headlines([headline])

    assert "Markets rally" in html
    assert "https://example.com/markets-rally" in html
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
