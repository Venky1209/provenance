"""Blog content scraper implementation.

Extracts article text, title, author, date, and description from
generic blog/article pages using BeautifulSoup heuristics.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from models import SourceType
from scrapers.base_scraper import BaseScraper, ScraperError


class BlogScraper(BaseScraper):
    source_type = SourceType.BLOG

    def scrape(self, url: str) -> dict[str, Any]:
        html = self.fetch_html(url)
        soup = BeautifulSoup(html, "lxml")

        title = self._extract_title(soup)
        author = self._extract_author(soup)
        published_date = self._extract_date(soup)
        description = self._extract_description(soup)
        raw_text = self._extract_body(soup)
        citations_count = self._count_citations(soup, raw_text)

        if not raw_text or len(raw_text.strip()) < 50:
            raise ScraperError(
                f"Insufficient article content from {url}",
                source_type=self.source_type.value,
            )

        return {
            "title": title,
            "author": author,
            "published_date": published_date,
            "description": description,
            "raw_text": raw_text,
            "citations_count": citations_count,
            "region": self._guess_region(url),
        }

    # ── Extraction helpers ────────────────────────────────────────

    def _extract_title(self, soup: BeautifulSoup) -> str:
        # Try og:title first, then <h1>, then <title>
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            return og["content"].strip()
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        title_tag = soup.find("title")
        return title_tag.get_text(strip=True) if title_tag else ""

    def _extract_author(self, soup: BeautifulSoup) -> str:
        # Schema.org author
        for selector in [
            {"name": "author"},
            {"property": "article:author"},
            {"name": "article:author"},
        ]:
            meta = soup.find("meta", attrs=selector)
            if meta and meta.get("content"):
                return meta["content"].strip()

        # Look for common author class patterns
        for cls in ["author", "byline", "post-author", "article-author"]:
            el = soup.find(class_=re.compile(cls, re.IGNORECASE))
            if el:
                text = el.get_text(strip=True)
                # Clean "By Author Name" prefix
                text = re.sub(r"^(by|written by|author:?)\s*", "", text, flags=re.IGNORECASE)
                if text and len(text) < 100:
                    return text

        # rel="author" link
        author_link = soup.find("a", rel="author")
        if author_link:
            return author_link.get_text(strip=True)

        return ""

    def _extract_date(self, soup: BeautifulSoup) -> str:
        # meta tags
        for attr in [
            {"property": "article:published_time"},
            {"name": "date"},
            {"name": "publish_date"},
            {"property": "og:published_time"},
            {"itemprop": "datePublished"},
        ]:
            meta = soup.find("meta", attrs=attr)
            if meta and meta.get("content"):
                return meta["content"].strip()[:10]

        # <time> element
        time_el = soup.find("time")
        if time_el:
            dt = time_el.get("datetime", "") or time_el.get_text(strip=True)
            if dt:
                return dt.strip()[:10]

        return ""

    def _extract_description(self, soup: BeautifulSoup) -> str:
        for attr in [
            {"property": "og:description"},
            {"name": "description"},
        ]:
            meta = soup.find("meta", attrs=attr)
            if meta and meta.get("content"):
                return meta["content"].strip()
        return ""

    def _extract_body(self, soup: BeautifulSoup) -> str:
        # Remove unwanted elements
        for tag in soup.find_all(["script", "style", "nav", "footer",
                                   "header", "aside", "iframe", "noscript"]):
            tag.decompose()

        # Try <article> first
        article = soup.find("article")
        if article:
            return article.get_text(separator="\n", strip=True)

        # Try main content area
        main = soup.find("main") or soup.find(id=re.compile("content|article|post", re.I))
        if main:
            return main.get_text(separator="\n", strip=True)

        # Fallback: largest text block
        body = soup.find("body")
        if body:
            return body.get_text(separator="\n", strip=True)

        return ""

    def _count_citations(self, soup: BeautifulSoup, text: str) -> int:
        """Count visible references, links to papers, and citation markers."""
        count = 0
        # Numbered references like [1], [2]
        count += len(re.findall(r"\[\d+\]", text))
        # DOI links
        count += len(soup.find_all("a", href=re.compile(r"doi\.org", re.I)))
        # PubMed links
        count += len(soup.find_all("a", href=re.compile(r"pubmed", re.I)))
        return count

    def _guess_region(self, url: str) -> str:
        """Best-effort region guess from TLD."""
        try:
            host = urlparse(url).hostname or ""
            tld = host.rsplit(".", 1)[-1].lower()
            tld_map = {
                "uk": "UK", "au": "Australia", "ca": "Canada",
                "in": "India", "de": "Germany", "fr": "France",
            }
            return tld_map.get(tld, "US")
        except Exception:
            return ""