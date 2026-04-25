# Architectural Decisions (DECISIONS.md)

This document outlines the key technical tradeoffs and decisions made while designing the Provenance data scraping and trust scoring pipeline.

## 1. Configurable Scraping Quantity & Source Agnosticism
**Decision:** The system uses a centralized `config.py` with a flexible dictionary (`TARGET_URLS`), allowing an arbitrary number of sources to be defined.
**Rationale:** Rather than hardcoding the 3 blogs, 2 YouTube videos, and 1 PubMed article requested by the assignment, the batch pipeline iterates over the configuration dynamically. Furthermore, the `POST /scrape` endpoint allows *any* URL to be scraped live. This transforms the project from a static homework script into a flexible, source-agnostic data pipeline.

## 2. Scraping Engine Selection (BeautifulSoup vs. Crawl4AI)
**Decision:** The primary scraping engine relies on `requests` and `BeautifulSoup4`/`lxml`. Crawl4AI (with Playwright) is introduced strictly as an *optional async fallback* for JavaScript-rendered SPAs (like Next.js or React sites).
**Rationale:** 
- **Speed & Deployment:** `requests` + BS4 is extremely lightweight, fast, and works flawlessly on minimal cloud environments like Railway.
- **The JS Problem:** Modern SPAs often return empty `<body>` tags without JavaScript execution.
- **The Tradeoff:** Crawl4AI is the leading open-source LLM-friendly web crawler and handles JS rendering perfectly. However, including Playwright adds ~400MB to the deployment image, drastically increasing cold start times and memory usage on Railway.
- **Resolution:** By making Crawl4AI an optional fallback inside the `BlogScraper`, the system stays fast and lightweight for 95% of requests, but has the architectural capability to handle complex dynamic sites when necessary.

## 3. Trust Score Transparency
**Decision:** The scoring algorithm returns a deterministic score along with a `trust_breakdown`, `risk_flags`, and a human-readable `scoring_reason`.
**Rationale:** Trust in data pipelines requires explainability (aligned with E-E-A-T and DISCERN principles). A black-box score is not useful for downstream consumers. By exposing the exact penalties (e.g., `seo_spam_pattern` or `missing_author`) and factor weights, the API allows consumers to audit the logic.

## 4. Dual API Surface
**Decision:** The FastAPI application exposes both static dataset endpoints (`GET /sources`) and a live interaction endpoint (`POST /scrape`).
**Rationale:** The assignment requires delivering the scraped data as JSON artifacts. Serving these statically ensures rapid, predictable review. The live `POST /scrape` endpoint powers the interactive dashboard, demonstrating that the scraping and scoring logic operates dynamically in real-time, fulfilling the role of a true API service.
