"""main.py

Run the Morning Digest pipeline end-to-end: ingest, summarise, and publish.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from commons import User
from database import Database
from ingester import FEEDS, Ingester
from organiser import Organiser
from summariser import Summariser
from top_extractor import TopExtractor


class DigestApp:
    """Coordinates ingestion, summarisation, and page generation."""

    DEFAULT_USERNAME = "default_user"
    DEFAULT_NAME = "Singapore"

    def __init__(self) -> None:
        self.parser = self._build_parser()
        self.db = Database()
        self.ingester = Ingester()
        self.summariser = Summariser()
        self.top_extractor = TopExtractor()

    def run(self, argv: Optional[List[str]] = None) -> None:
        args = self.parser.parse_args(argv)
        self._ensure_default_user()
        self.ingester.populate_feeds()

        users = list(self.db.get_all())
        if not users:
            print("No users found. Add at least one user to proceed.")
            return

        print(f"Generating digests for {len(users)} user(s)")
        self.top_extractor.pick_top_articles(users)
        self.summariser.summarise(users)
        
        for user in users:
            output_path = self._output_path(args.output, user)
            Organiser.build(user=user, output_file=output_path)
            print(f"✉️  Built digest for {user.name or user.username} -> {output_path}")

    # ------------------------------------------------------------------
    # Argument parsing
    # ------------------------------------------------------------------
    @staticmethod
    def _build_parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="morning-digest")
        parser.add_argument(
            "--output",
            "-o",
            default="output/morning_digest.md",
            help="Base output Markdown file path",
        )
        return parser

    # ------------------------------------------------------------------
    # Users & feeds
    # ------------------------------------------------------------------
    def _ensure_default_user(self) -> None:
        if self.db.is_present(self.DEFAULT_USERNAME):
            return
        self.db.add(
            username=self.DEFAULT_USERNAME,
            name=self.DEFAULT_NAME,
            selected_feeds=self._all_feed_names(),
        )

    @staticmethod
    def _all_feed_names() -> Sequence[str]:
        return [feed.name for feed in FEEDS]

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _output_path(base: str, user: User) -> str:
        slug_source = user.name or user.username or "reader"
        slug = "".join(char if char.isalnum() else "_" for char in slug_source).lower()
        base_path = Path(base)
        if base_path == Path("output/morning_digest.md"):
            return str(Path(f"output/morning_digest_{slug}.md"))
        return str(base_path.with_name(base_path.stem + f"_{slug}" + base_path.suffix))


def main(argv: Optional[List[str]] = None) -> None:
    app = DigestApp()
    app.run(argv)

if __name__ == "__main__":
    main(sys.argv[1:])
