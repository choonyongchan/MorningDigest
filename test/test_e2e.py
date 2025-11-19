import organiser as organiser_module
import main as main_module
from commons import Article, Feed, User


class MemoryDatabase:
    def __init__(self):
        self.user_record = None

    def is_present(self, _username):
        return self.user_record is not None

    def add(self, username, name, selected_feeds):
        feed = Feed(
            name="E2E Feed",
            tags=["e2e"],
            url="https://example.com/feed",
            article=[
                Article(
                    title="E2E story",
                    summary="E2E summary",
                    published="Mon, 01 Jan 2024 00:00:00 GMT",
                )
            ],
        )
        self.user_record = User(username=username, name=name, selected_feeds=[feed])

    def get_all(self):
        return [self.user_record] if self.user_record else []


class StubIngester:
    instances = []

    def __init__(self):
        StubIngester.instances.append(self)
        self.populate_called = False

    def populate_feeds(self):
        self.populate_called = True


class StubSummariser:
    instances = []

    def __init__(self):
        StubSummariser.instances.append(self)

    def summarise(self, users):
        for user in users:
            user.summary = "E2E generated summary"


class DummyQuoteResponse:
    def raise_for_status(self):  # pragma: no cover - no network in tests
        return None

    def json(self):
        return [{"q": "Forward ever.", "a": "E2E Bot"}]


def test_cli_end_to_end(monkeypatch, tmp_path):
    monkeypatch.setattr(main_module, "Database", MemoryDatabase)
    monkeypatch.setattr(main_module, "Ingester", StubIngester)
    monkeypatch.setattr(main_module, "Summariser", StubSummariser)

    def fake_get(*_args, **_kwargs):
        return DummyQuoteResponse()

    monkeypatch.setattr(organiser_module.requests, "get", fake_get)

    output_path = tmp_path / "digest.md"

    main_module.main(["--output", str(output_path)])

    # The actual file has a user-specific suffix
    actual_output = tmp_path / "digest_singapore.md"
    assert actual_output.exists()
    content = actual_output.read_text(encoding="utf-8")
    assert "E2E generated summary" in content
    assert "E2E story" in content
    assert StubIngester.instances and StubIngester.instances[0].populate_called
