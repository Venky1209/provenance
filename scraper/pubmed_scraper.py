"""PubMed abstract and metadata scraper implementation.

Uses NCBI Entrez E-utilities (via Biopython) to fetch structured
article metadata and abstracts from PubMed IDs.
"""

from __future__ import annotations

import re
from typing import Any

from Bio import Entrez
from bs4 import BeautifulSoup

from models import SourceType
from scraper.base_scraper import BaseScraper, ScraperError

# Required by NCBI — use a real email for production
Entrez.email = "provenance-scraper@example.com"


class PubMedScraper(BaseScraper):
    source_type = SourceType.PUBMED

    def scrape(self, url: str) -> dict[str, Any]:
        pmid = self._extract_pmid(url)
        if not pmid:
            raise ScraperError(
                f"Cannot extract PMID from {url}",
                source_type=self.source_type.value,
            )

        try:
            return self._fetch_via_entrez(pmid)
        except Exception as exc:
            # Fallback: try HTML scraping
            try:
                return self._fetch_via_html(url, pmid)
            except Exception:
                raise ScraperError(
                    f"Failed to fetch PubMed article {pmid}: {exc}",
                    source_type=self.source_type.value,
                )

    def _extract_pmid(self, url: str) -> str | None:
        """Extract PubMed ID from URL."""
        match = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", url)
        if match:
            return match.group(1)
        match = re.search(r"PMID[:\s]*(\d+)", url, re.IGNORECASE)
        if match:
            return match.group(1)
        # If the URL is just a number
        match = re.search(r"/(\d{6,10})/?$", url)
        if match:
            return match.group(1)
        return None

    def _fetch_via_entrez(self, pmid: str) -> dict[str, Any]:
        """Use Biopython Entrez to get structured article data."""
        handle = Entrez.efetch(db="pubmed", id=pmid, rettype="xml", retmode="xml")
        raw_xml = handle.read()
        handle.close()

        # Parse as string if bytes
        if isinstance(raw_xml, bytes):
            raw_xml = raw_xml.decode("utf-8")

        soup = BeautifulSoup(raw_xml, "lxml-xml")

        # Title
        title_el = soup.find("ArticleTitle")
        title = title_el.get_text(strip=True) if title_el else ""

        # Authors
        authors = []
        for author_el in soup.find_all("Author"):
            last = author_el.find("LastName")
            fore = author_el.find("ForeName") or author_el.find("Initials")
            col = author_el.find("CollectiveName")
            if last:
                name = last.get_text(strip=True)
                if fore:
                    name = f"{fore.get_text(strip=True)} {name}"
                authors.append(name)
            elif col:
                authors.append(col.get_text(strip=True))
        author_str = ", ".join(authors) if authors else ""

        # Journal
        journal_el = soup.find("Journal")
        journal = ""
        if journal_el:
            jtitle = journal_el.find("Title")
            journal = jtitle.get_text(strip=True) if jtitle else ""

        # Date
        pub_date = ""
        date_el = soup.find("PubDate")
        if date_el:
            year = date_el.find("Year")
            month = date_el.find("Month")
            day = date_el.find("Day")
            parts = []
            if year:
                parts.append(year.get_text(strip=True))
            if month:
                parts.append(month.get_text(strip=True))
            if day:
                parts.append(day.get_text(strip=True))
            pub_date = "-".join(parts)

        # Abstract
        abstract_el = soup.find("AbstractText")
        abstract = ""
        if abstract_el:
            abstract = abstract_el.get_text(strip=True)
        else:
            # Try multiple AbstractText elements (structured abstract)
            abstract_parts = soup.find_all("AbstractText")
            if abstract_parts:
                abstract = " ".join(p.get_text(strip=True) for p in abstract_parts)

        # Citation count (references)
        refs = soup.find_all("ArticleId", IdType="pubmed")
        citations_count = max(0, len(refs) - 1)  # exclude self

        return {
            "title": title,
            "author": author_str,
            "published_date": pub_date,
            "description": abstract[:300] if abstract else "",
            "raw_text": abstract,
            "journal": journal,
            "citations_count": citations_count,
            "region": "US",
        }

    def _fetch_via_html(self, url: str, pmid: str) -> dict[str, Any]:
        """Fallback: scrape the PubMed web page directly."""
        html = self.fetch_html(url)
        soup = BeautifulSoup(html, "lxml")

        title = ""
        h1 = soup.find("h1", class_="heading-title")
        if h1:
            title = h1.get_text(strip=True)

        # Authors
        authors_div = soup.find("div", class_="authors-list")
        author_str = ""
        if authors_div:
            author_links = authors_div.find_all("a", class_="full-name")
            author_str = ", ".join(a.get_text(strip=True) for a in author_links)

        # Date
        date_el = soup.find("span", class_="cit")
        pub_date = ""
        if date_el:
            text = date_el.get_text(strip=True)
            date_match = re.search(r"(\d{4}\s+\w+(\s+\d{1,2})?)", text)
            if date_match:
                pub_date = date_match.group(1)

        # Journal
        journal_el = soup.find("button", id="full-view-journal-trigger")
        journal = journal_el.get_text(strip=True) if journal_el else ""

        # Abstract
        abstract_div = soup.find("div", class_="abstract-content")
        abstract = abstract_div.get_text(separator=" ", strip=True) if abstract_div else ""

        return {
            "title": title,
            "author": author_str,
            "published_date": pub_date,
            "description": abstract[:300] if abstract else "",
            "raw_text": abstract,
            "journal": journal,
            "citations_count": 0,
            "region": "US",
        }