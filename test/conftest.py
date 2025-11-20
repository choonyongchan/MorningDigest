from pathlib import Path
import sys
from types import SimpleNamespace
import types
from importlib.machinery import ModuleSpec

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

if "openai" not in sys.modules:
    def _dummy_create(**_kwargs):
        return SimpleNamespace(output_text="")

    class _DummyClient:
        def __init__(self):
            self.responses = SimpleNamespace(create=_dummy_create)

    dummy_module = types.ModuleType("openai")
    dummy_module.__spec__ = ModuleSpec(name="openai", loader=None)
    dummy_module.OpenAI = _DummyClient
    sys.modules["openai"] = dummy_module

from commons import Article, Feed, User  # noqa: E402
import pytest  # noqa: E402


@pytest.fixture
def sample_feed() -> Feed:
    return Feed(
        name="Sample Feed",
        tags=["sample"],
        url="https://example.com/feed",
        article=[
            Article(
                title="Sample Story",
                url="https://example.com/articles/sample-story",
                published="Mon, 01 Jan 2024 08:00:00 GMT",
                summary="Sample summary",
            )
        ],
    )


@pytest.fixture
def sample_user(sample_feed: Feed) -> User:
    return User(
        username="janedoe",
        name="Jane Doe",
        selected_feeds=[sample_feed],
        summary="Sample personalised summary.",
        top_articles=sample_feed.article,
    )
