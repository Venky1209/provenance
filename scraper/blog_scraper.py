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
from scraper.base_scraper import BaseScraper, ScraperError


class InsufficientContentError(ScraperError):
    pass


class BlogScraper(BaseScraper):
    source_type = SourceType.BLOG

    def scrape(self, url: str) -> dict[str, Any]:
        try:
            # Primary: fast, lightweight, no browser needed (good for Railway)
            return self._scrape_with_requests(url)
        except InsufficientContentError:
            # Page requires JS rendering (SPA/React/Qualtrics/etc.)
            try:
                import asyncio
                # Set up a new event loop if needed (for thread safety in FastAPI)
                return asyncio.run(self._scrape_with_crawl4ai(url))
            except Exception as e:
                # If crawl4ai fails or isn't installed properly, return a graceful partial result
                return self._js_fallback_result(url, error=str(e))

    def _scrape_with_requests(self, url: str) -> dict[str, Any]:
        html = self.fetch_html(url)
        soup = BeautifulSoup(html, "lxml")

        title = self._extract_title(soup)
        author = self._extract_author(soup)
        published_date = self._extract_date(soup)
        description = self._extract_description(soup)
        raw_text = self._extract_body(soup)
        citations_count = self._count_citations(soup, raw_text)

        if not raw_text or len(raw_text.strip()) < 50:
            raise InsufficientContentError(
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

        # Fallback to extracting all <p> text
        p_tags = soup.find_all("p")
        if p_tags:
            return "\n".join(p.get_text(separator=" ", strip=True) for p in p_tags)

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

    async def _scrape_with_crawl4ai(self, url: str) -> dict[str, Any]:
        """
        Actually use Crawl4AI to render the JS and extract content.
        """
        from crawl4ai import AsyncWebCrawler
        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(url=url, bypass_cache=True)
            
            # If crawl4ai also fails to find content
            if not result.markdown or len(result.markdown.strip()) < 50:
                raise InsufficientContentError(f"Crawl4AI found no content for {url}")

            metadata = result.metadata or {}
            
            return {
                "title": metadata.get("title") or metadata.get("og:title") or f"Scraped Page: {url}",
                "author": metadata.get("author") or "",
                "published_date": metadata.get("published_date") or metadata.get("og:published_time") or "",
                "description": metadata.get("description") or metadata.get("og:description") or "",
                "raw_text": result.markdown,
                "citations_count": 0,  # Markdown citations are harder to count via regex
                "region": self._guess_region(url),
                "_is_js_rendered": True
            }

    def _js_fallback_result(self, url: str, error: str | None = None) -> dict[str, Any]:
        """
        Graceful fallback for JS-only pages if rendering fails.
        """
        from urllib.parse import urlparse
        host = urlparse(url).hostname or url
        error_msg = f" (Error: {error})" if error else ""
        return {
            "title": f"JS-only page: {host}",
            "author": "",
            "published_date": "",
            "description": (
                f"This URL ({host}) requires a JavaScript runtime. "
                f"Headless rendering failed or was skipped{error_msg}. "
                "No readable text was extracted."
            ),
            "raw_text": f"Page at {url} requires JavaScript rendering. Rendering failed{error_msg}.",
            "citations_count": 0,
            "region": self._guess_region(url),
            "_risk_flags": ["js_rendering_required", "missing_author", "missing_date"],
        }

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