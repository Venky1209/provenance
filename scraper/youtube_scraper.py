"""YouTube transcript and metadata scraper implementation.

Uses youtube-transcript-api for transcripts and page scraping for
metadata (title, channel, date, description).
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from models import SourceType
from scraper.base_scraper import BaseScraper, ScraperError, DEFAULT_HEADERS, DEFAULT_TIMEOUT

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    HAS_TRANSCRIPT_API = True
except ImportError:
    HAS_TRANSCRIPT_API = False


class YouTubeScraper(BaseScraper):
    source_type = SourceType.YOUTUBE

    def scrape(self, url: str) -> dict[str, Any]:
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ScraperError(
                f"Cannot extract video ID from {url}",
                source_type=self.source_type.value,
            )

        metadata = self._fetch_metadata(url, video_id)
        transcript, transcript_available = self._fetch_transcript(video_id)

        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("channel", ""),
            "published_date": metadata.get("date", ""),
            "description": metadata.get("description", ""),
            "raw_text": transcript or metadata.get("description", ""),
            "citations_count": 0,
            "region": "",
            "transcript_available": transcript_available,
        }

    def _extract_video_id(self, url: str) -> str | None:
        """Parse YouTube video ID from various URL formats."""
        parsed = urlparse(url)
        if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
            qs = parse_qs(parsed.query)
            return qs.get("v", [None])[0]
        if parsed.hostname == "youtu.be":
            return parsed.path.lstrip("/")
        return None

    def _fetch_metadata(self, url: str, video_id: str) -> dict[str, str]:
        """Scrape video metadata from the YouTube page and oEmbed."""
        meta: dict[str, str] = {}

        # Try oEmbed API first (lightweight, no HTML parsing)
        try:
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            resp = requests.get(oembed_url, timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                meta["title"] = data.get("title", "")
                meta["channel"] = data.get("author_name", "")
        except Exception:
            pass

        # Scrape the page for date and description
        try:
            html = self.fetch_html(url)
            soup = BeautifulSoup(html, "lxml")

            if not meta.get("title"):
                og_title = soup.find("meta", property="og:title")
                meta["title"] = og_title["content"].strip() if og_title and og_title.get("content") else ""

            if not meta.get("channel"):
                link = soup.find("link", itemprop="name")
                meta["channel"] = link.get("content", "") if link else ""

            # Date from meta or page content
            date_meta = soup.find("meta", itemprop="datePublished")
            if date_meta and date_meta.get("content"):
                meta["date"] = date_meta["content"][:10]
            else:
                date_meta = soup.find("meta", property="og:video:release_date")
                if date_meta and date_meta.get("content"):
                    meta["date"] = date_meta["content"][:10]

            # Description
            og_desc = soup.find("meta", property="og:description")
            meta["description"] = og_desc["content"].strip() if og_desc and og_desc.get("content") else ""

        except Exception:
            pass

        return meta

    def _fetch_transcript(self, video_id: str) -> tuple[str, bool]:
        """Attempt to fetch transcript. Returns (text, was_available)."""
        if not HAS_TRANSCRIPT_API:
            return "", False

        try:
            # Handle different versions of youtube-transcript-api
            if hasattr(YouTubeTranscriptApi, 'get_transcript'):
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                segments = [item['text'] for item in transcript_list]
            else:
                transcript_list = YouTubeTranscriptApi().fetch(video_id)
                segments = [item.text for item in transcript_list]
            return " ".join(segments), True
        except Exception:
            return "", False