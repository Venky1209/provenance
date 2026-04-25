"""Shared scraper interface and common source behavior.

Defines the abstract contract that all source-specific scrapers implement,
plus shared timeout and error handling logic.
"""

from __future__ import annotations

import abc
from typing import Any

import requests

from models import SourceType

DEFAULT_TIMEOUT = 15
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class ScraperError(Exception):
    """Raised when a scraper cannot produce usable output."""

    def __init__(self, message: str, source_type: str | None = None):
        self.source_type = source_type
        super().__init__(message)


class BaseScraper(abc.ABC):
    """Abstract base for all source scrapers."""

    source_type: SourceType

    def fetch_html(self, url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
        """GET a URL and return raw HTML. Raises ScraperError on failure."""
        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        except requests.Timeout:
            raise ScraperError(
                f"Timeout after {timeout}s fetching {url}",
                source_type=self.source_type.value,
            )
        except requests.RequestException as exc:
            raise ScraperError(
                f"Failed to fetch {url}: {exc}",
                source_type=self.source_type.value,
            )

    @abc.abstractmethod
    def scrape(self, url: str) -> dict[str, Any]:
        """Scrape *url* and return a raw metadata dict.

        Must include at minimum: title, author, published_date, raw_text.
        May include: description, journal, citations_count, region.
        """
        ...