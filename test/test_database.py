"""Tests for the SQLite-backed Database helper."""

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

import database as database_module  # noqa: E402
from commons import Feed  # noqa: E402


@dataclass
class _TestUser:
    username: str
    name: str
    selected_feeds: Sequence[Feed]


@pytest.fixture()
def database(tmp_path, monkeypatch):
    """Return a Database instance backed by a temporary SQLite file."""

    monkeypatch.setattr(database_module, "User", _TestUser)
    db_path = tmp_path / "users.db"
    db = database_module.Database(path=str(db_path))
    try:
        yield db
    finally:
        db.conn.close()


def test_add_and_get_all(database):
    database.add("alice", "Alice", ["StraitsTimes World", "ChannelNewsAsia Business"])

    users = database.get_all()

    assert len(users) == 1
    user = users[0]
    assert user.username == "alice"
    assert user.name == "Alice"
    assert [feed.name for feed in user.selected_feeds] == [
        "StraitsTimes World",
        "ChannelNewsAsia Business",
    ]


def test_duplicate_username_raises(database):
    database.add("bob", "Bob", ["StraitsTimes World"])

    with pytest.raises(ValueError):
        database.add("bob", "Robert", ["StraitsTimes Life"])


def test_delete_user_removes_entry(database):
    database.add("carol", "Carol", ["StraitsTimes Life"])
    database.add("dave", "Dave", ["StraitsTimes Asia", "ChannelNewsAsia Sport"])

    database.delete("carol")
    usernames = {user.username for user in database.get_all()}

    assert usernames == {"dave"}


def test_update_user_modifies_name_and_feeds(database):
    database.add("eve", "Eve", ["ChannelNewsAsia Latest"])

    database.update(
        "eve",
        name="Evelyn",
        selected_feeds=["StraitsTimes Tech", "ChannelNewsAsia World"],
    )
    updated = database.get_all()[0]

    assert updated.name == "Evelyn"
    assert [feed.name for feed in updated.selected_feeds] == [
        "StraitsTimes Tech",
        "ChannelNewsAsia World",
    ]


def test_serialisation_round_trip():
    feeds = ["World", "Business"]

    payload = database_module.Database.serialise_feeds(feeds)
    restored = database_module.Database.deserialise_feeds(payload)

    assert restored == feeds
