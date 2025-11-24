"""Compose the Morning Digest output using rounded boxes and a centered header."""

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import List, Optional

import requests

from commons import Quote, User


@dataclass(frozen=True)
class Headline:
    title: str
    url: str

@dataclass(frozen=True)
class DigestContent:
    name: str
    summary: str
    sponsor_name: str
    sponsor_message: str
    partnership_message: str
    top_headlines: List[Headline]

class Organiser:
    """Create a one-page digest using modular rounded sections."""

    LOGO_PATH: str = "img/MorningDigest.png" 
    SPONSOR_NAME: str = "Choonyong Chan"
    SPONSOR_MESSAGE: str = "❤️ This edition is made possible by friends of The Morning Digest."
    PARTNERSHIP_MESSAGE: str = "📬 Forward this digest to someone who should wake up informed."
    EN_CHINESE_TRANSLATION_LINK: str = "https://choonyongchan-github-io.translate.goog/MorningDigest/?_x_tr_sl=en&_x_tr_tl=zh-CN"
    EN_MALAY_TRANSLATION_LINK: str = "https://choonyongchan-github-io.translate.goog/MorningDigest/?_x_tr_sl=en&_x_tr_tl=ms"
    EN_TAMIL_TRANSLATION_LINK: str = "https://choonyongchan-github-io.translate.goog/MorningDigest/?_x_tr_sl=en&_x_tr_tl=ta"

    @staticmethod
    def build(
        user: User,
        output_file: str,
    ) -> None:
        top_headlines = Organiser.build_top_headlines(user)
        content = DigestContent(
            name=user.name,
            summary=user.summary,
            sponsor_name=Organiser.SPONSOR_NAME,
            sponsor_message=Organiser.SPONSOR_MESSAGE,
            partnership_message=Organiser.PARTNERSHIP_MESSAGE,
            top_headlines=top_headlines,
        )
        markdown_text = Organiser._compose_markdown(content)
        Organiser._write(output_file, markdown_text)

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _compose_markdown(content: DigestContent) -> str:
        quote = Organiser.get_daily_quote()
        header = Organiser.build_header(content.name, content.sponsor_name, quote)
        sections = [
            Organiser._rounded_box(f"Good Morning {content.name}", Organiser.build_good_morning(content.summary)),
            Organiser._rounded_box(f"Presented by {content.sponsor_name}", Organiser.build_sponsor(content.sponsor_message)),
            Organiser._rounded_box("Top Headlines", Organiser.build_headlines(content.top_headlines)),
            Organiser._rounded_box("Partnership + Share", Organiser.build_partnership_share(content.partnership_message)),
        ]
        return "\n\n".join(filter(None, [Organiser._style_block(), header, *sections]))

    @staticmethod
    def _style_block() -> str:
        return (
            "<style>\n"
            "body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 0; padding: 24px; background: #f4f1ec; }\n"
            ".digest-header { text-align: center; margin-bottom: 24px; }\n"
            ".digest-header img { max-width: 180px; height: auto; display: block; margin: 0 auto 8px; }\n"
            ".digest-header h1 { margin: 6px 0; font-size: 28px; }\n"
            ".digest-header .sponsor-line { font-weight: 600; margin: 6px 0; }\n"
            ".digest-header .quote-text { font-size: 18px; font-style: italic; margin: 12px 0 4px; }\n"
            ".digest-header .quote-meta { color: #4b5d52; margin: 0; }\n"
            ".digest-box { background: #e8f5e9; border-radius: 18px; padding: 18px 20px; margin: 18px 0; border: 1px solid #c8e6c9; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }\n"
            ".digest-box h3 { margin-top: 0; margin-bottom: 12px; color: #1b5e20; }\n"
            ".digest-box ul { padding-left: 20px; margin: 0; }\n"
            ".digest-box p { margin: 10px 0; line-height: 1.5; }\n"
            ".headline-meta { display: block; font-size: 12px; color: #4b5d52; }\n"
            "</style>"
        )
    
    @staticmethod
    def _rounded_box(title: str, body_html: str) -> str:
        return (
            "<div class='digest-box'>\n"
            f"<h3>{title}</h3>\n"
            f"{body_html}\n"
            "</div>"
        )
    
    @staticmethod
    def _paragraphs(paragraphs: List[str]) -> str:
        return "\n".join(f"<p>{para}</p>" for para in paragraphs)

    @staticmethod
    def get_daily_quote() -> Quote:
        quote = "Keep going — small steps also reach Marina Bay."
        author = "Unknown"
        try:
            response = requests.get("https://zenquotes.io/api/today", timeout=5)
            response.raise_for_status()
            payload = response.json()
            quote = payload[0].get("q", quote).strip()
            author = payload[0].get("a", author).strip()
        except Exception:
            pass
        return Quote(quote, author)

    @staticmethod
    def build_logo() -> str:
        logo_path = Path(Organiser.LOGO_PATH)
        if not logo_path.exists():
            return "<h1 style='margin:0;'>The Morning Digest</h1>"
        encoded = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
        return (
            "<img src='data:image/png;base64,"
            f"{encoded}' alt='The Morning Digest Logo' />"
        )

    @staticmethod
    def build_header(user_name: str, sponsor_name: str, quote: Quote) -> str:
        logo_html = Organiser.build_logo()
        date_html = f"<p class='sponsor-line'>{datetime.now().strftime('%A, %d %B %Y')}</p>"
        sponsor_html = f"<p class='sponsor-line'>Together with <strong>{sponsor_name}</strong></p>"
        quote_html = (
            "<div class='header-quote'>"
            f"<p class='quote-text'>“{quote.quote}”</p>"
            f"<p class='quote-meta'>— {quote.author}</p>"
            "</div>"
        )
        translations_html = (
            f"""<p class='quote-meta'>
            <a href='{Organiser.EN_CHINESE_TRANSLATION_LINK}'>中文</a> |
            <a href='{Organiser.EN_MALAY_TRANSLATION_LINK}'>Bahasa Melayu</a> |
            <a href='{Organiser.EN_TAMIL_TRANSLATION_LINK}'>தமிழ்</a> 
            </p>"""
        )
        name = "" if user_name == "Singapore" else f" for {user_name}"
        return (
            "<div class='digest-header'>\n"
            f"{logo_html}\n"
            f"<h1>The Morning Digest{name}</h1>\n"
            f"{date_html}"
            f"{sponsor_html}\n"
            f"{quote_html}\n"
            f"{translations_html}\n"
            "</div>"
        )

    @staticmethod
    def build_good_morning(summary: str) -> str:
        text = (summary or "").strip()
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = ["Summary is currently unavailable."]
        return Organiser._paragraphs(paragraphs)

    @staticmethod
    def build_sponsor(message: str) -> str:
        return Organiser._paragraphs([message])

    @staticmethod
    def build_headlines(headlines: List[Headline]) -> str:
        if not headlines:
            return "<p>No fresh headlines right now — check back soon.</p>"
        items = []
        for head in headlines:
            items.append(
                "<li>"
                f"<a href='{head.url}'>{head.title}</a>"
                "</li>"
            )
        return f"<ul>{''.join(items)}</ul>"

    @staticmethod
    def build_partnership_share(message: str) -> str:
        parts = [
            f"<p>{message}</p>",
            "<p>🤝 Partner with us: <a href='#'>Submit a sponsorship enquiry →</a></p>",
            "<p>✨ Share with a friend: forwarding is the best compliment.</p>",
            "<p>🌏 Got a story? Tell us about SG or regional stories we should feature.</p>",
        ]
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Headlines aggregation
    # ------------------------------------------------------------------
    
    @staticmethod
    def build_top_headlines(user: User) -> List[Headline]:
        return [
            Headline(title=article.title, url=article.url) 
            for article in user.top_articles
        ]
        
    @staticmethod
    def _parse_datetime(value: Optional[str]) -> datetime:
        if not value:
            return datetime.min.replace(tzinfo=timezone.utc)
        for parser in (Organiser._parse_iso, Organiser._parse_rfc2822):
            parsed = parser(value)
            if parsed is not None:
                return parsed
        return datetime.min.replace(tzinfo=timezone.utc)

    @staticmethod
    def _parse_iso(value: str) -> Optional[datetime]:
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return None

    @staticmethod
    def _parse_rfc2822(value: str) -> Optional[datetime]:
        try:
            dt = parsedate_to_datetime(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (TypeError, ValueError):
            return None

    # ------------------------------------------------------------------
    # IO helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _write(output_file: str, markdown_text: str) -> None:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists():
            output_path.unlink()
        output_path.write_text(markdown_text, encoding="utf-8")


def build(
    user: User,
    output_file: str = "output/morning_digest.md",
) -> str:
    return Organiser.build(user=user, output_file=output_file)