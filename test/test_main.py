from pathlib import Path
from types import SimpleNamespace

import main as main_module
from commons import Article, Feed, User


def test_digest_app_run_executes_pipeline(monkeypatch, tmp_path):
    add_calls = []

    class FakeDatabase:
        def __init__(self):
            self.added = False

        def is_present(self, username):
            return self.added if username == main_module.DigestApp.DEFAULT_USERNAME else False

        def add(self, username, name, selected_feeds):
            add_calls.append((username, name, tuple(selected_feeds)))
            self.added = True

        def get_all(self):
            feed = Feed(
                name="Sample Feed",
                tags=["sample"],
                url="https://example.com/feed",
                article=[Article(title="Story", summary="Summary")],
            )
            user = User(username="default_user", name="Morning Reader", selected_feeds=[feed], summary="")
            return [user]

    class FakeIngester:
        def __init__(self):
            self.populate_called = False

        def populate_feeds(self):
            self.populate_called = True

    class FakeSummariser:
        def __init__(self):
            self.called_with = None

        def summarise(self, users):
            self.called_with = list(users)
            for user in users:
                user.summary = "Unit test summary"

    built_users = []

    class FakeOrganiser:
        @staticmethod
        def build(user, output_file):
            built_users.append((user.username, user.summary, output_file))

    monkeypatch.setattr(main_module, "Database", FakeDatabase)
    monkeypatch.setattr(main_module, "Ingester", FakeIngester)
    monkeypatch.setattr(main_module, "Summariser", FakeSummariser)
    monkeypatch.setattr(main_module, "Organiser", FakeOrganiser)

    app = main_module.DigestApp()
    app.parser.parse_args = lambda _argv: SimpleNamespace(output=str(tmp_path / "digest.md"))

    app.run([])

    assert add_calls and add_calls[0][0] == main_module.DigestApp.DEFAULT_USERNAME
    assert built_users and built_users[0][1] == "Unit test summary"


def test_output_path_variants(tmp_path):
    user = User(username="abc", name="Alice", selected_feeds=[])
    default_path = main_module.DigestApp._output_path("output/morning_digest.md", user)
    custom_path = main_module.DigestApp._output_path(str(tmp_path / "custom.md"), user)

    assert default_path.endswith("morning_digest_alice.md")
    assert custom_path.endswith("custom_alice.md")
