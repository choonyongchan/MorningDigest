from dataclasses import dataclass
from typing import Optional, Sequence

@dataclass
class Article:
    title: str # Article Title
    url: str # Article URL
    published: Optional[str] = None # Published Date
    summary: Optional[str] = None # Article Summary

@dataclass
class Feed:
    name: str # Feed Name
    tags: Sequence[str] # Descriptions of Feed
    url: str # Feed Source URL
    article: Optional[Sequence[Article]] = None # Raw fetched content

@dataclass
class User:
    username: str # Unique, used as primary key
    name: str # Preferred Name 
    selected_feeds: Sequence[Feed] # Selected Feeds of interest
    summary: Optional[str] = None # Collated Summary
    top_articles: Optional[Sequence[Article]] = None # Top Headlines
    morning_digest: Optional[str] = None # Final Webpage content

@dataclass
class Quote:
    quote: str
    author: str