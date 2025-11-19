import os
from openai import OpenAI
from typing import List, Sequence

from commons import User, Feed


class Summariser:
    """Create concise newsletter summaries using GPT-5-Nano."""

    CLIENT = OpenAI()

    def __init__(
        self,
        model: str = "gpt-5-nano",
    ) -> None:
        self.check_api_key()

        self.client = self.CLIENT
        self.model = model

    @staticmethod
    def check_api_key():
        if not os.environ.get("OPENAI_API_KEY"):
            raise EnvironmentError("OPENAI_API_KEY not set in environment.")

    @staticmethod
    def feed_to_str(selected_feeds: Sequence[Feed]) -> str:
        articles = [
            f"{feed.name}: {article.title}: {article.summary or ''}"
            for feed in selected_feeds
            for article in feed.article
        ]
        return "\n\n".join(articles)

    def invoke_model(self, instructions: str, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=prompt,
        )
        return response.output_text or ""
        
    def summarise(self, users: List[User]) -> None:
        for user in users:
            selected_feeds = user.selected_feeds
            if not selected_feeds:
                continue
            prompt: str = self.feed_to_str(selected_feeds)
            instructions = (
                "You are a friendly and personal morning newsletter writer for a Singapore audience. "
                f"Write 3 short, engaging paragraphs summarising the following items for {user.name}. "
                f"Be concise, human, and lightly opinionated. Use simple language and a warm tone. Begin with 'Good Morning {user.name}!' "
            )
            summary = self.invoke_model(instructions, prompt)
            user.summary = summary.strip()
            
