import json
import sqlite3
from pathlib import Path
from typing import Optional, Sequence

from commons import Feed, User
from ingester import Ingester

class Database:
    """SQLite-backed user store for Morning Digest."""

    @staticmethod
    def serialise_feeds(feeds: Sequence[str]) -> str:
        return json.dumps(feeds, ensure_ascii=False)

    @staticmethod
    def deserialise_feeds(payload: str) -> Sequence[str]:
        return json.loads(payload)

    def __init__(self, path: str = "data/users.db") -> None:
        self.db_path = Path(path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.create()

    def create(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                selected_feeds TEXT NOT NULL
            )
            """
        )
    
    def is_present(self, username: str) -> bool:
        cursor = self.conn.execute(
            "SELECT 1 FROM users WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
        return row is not None

    def add(
        self,
        username: str,
        name: str,
        selected_feeds: Sequence[str],
    ) -> None:
        if self.is_present(username):
            raise ValueError(f"User with username '{username}' already exists.")
        serialized_feeds = self.serialise_feeds(selected_feeds)
        self.cursor.execute(
            "INSERT INTO users (username, name, selected_feeds) VALUES (?, ?, ?)",
            (username, name, serialized_feeds),
        )
        self.conn.commit()

    def delete(self, username: str) -> None:
        self.cursor.execute(
            "DELETE FROM users WHERE username = ?",
            (username,),
        )
        self.conn.commit()

    def update(self, username: str, name: Optional[str] = None, selected_feeds: Optional[Sequence[str]] = None) -> None:
        if not self.is_present(username):
            raise ValueError(f"User with username '{username}' does not exist.")
        if name is not None:
            self.cursor.execute(
                "UPDATE users SET name = ? WHERE username = ?",
                (name, username),
            )
        if selected_feeds is not None:
            serialized_feeds = self.serialise_feeds(selected_feeds)
            self.cursor.execute(
                "UPDATE users SET selected_feeds = ? WHERE username = ?",
                (serialized_feeds, username),
            )
        self.conn.commit()

    def get_all(self) -> Sequence[User]:
        self.cursor.execute("SELECT username, name, selected_feeds FROM users")
        rows = self.cursor.fetchall()
        users = []
        for row in rows:
            username, name, selected_feeds_json = row
            selected_feeds_json: Sequence[str] = self.deserialise_feeds(selected_feeds_json)
            selected_feeds: Sequence[Feed] = Ingester.match_feeds(selected_feeds_json)
            user: User = User(username=username, name=name, selected_feeds=selected_feeds)
            users.append(user)
        return users
    