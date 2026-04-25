# Technical Report: Provenance — Data Scraping & Trust Scoring System

## 1. Scraping Strategy

### Multi-Source Architecture

The system uses a **source-specific scraper pattern** where each content type (blog, YouTube, PubMed) has a dedicated scraper class inheriting from a shared `BaseScraper`. This design was chosen over a generic crawler because each source has fundamentally different content structures:

- **Blogs** are scraped via HTTP GET with BeautifulSoup4 and lxml. Content extraction follows a priority chain: `<article>` → `<main>` → `#content` → `<body>`. Metadata is extracted from OpenGraph tags, structured data, and common CSS class patterns (`.author`, `.byline`). Navigation, ads, and footer noise are stripped using regex patterns.

- **YouTube** uses a dual approach: the oEmbed API for lightweight title/channel metadata (no API key required), and the `youtube-transcript-api` library for transcript retrieval. When transcripts are unavailable (private captions, music videos), the system degrades gracefully — returning the video description as fallback text and flagging `transcript_unavailable` as a risk flag.

- **PubMed** uses Biopython's Entrez E-utilities to fetch structured XML directly from NCBI. This returns clean, pre-structured data (authors, journal, abstract, dates) without HTML parsing heuristics. A fallback HTML scraper exists for resilience if the Entrez API is unreachable.

### Content Processing Pipeline

After scraping, every source goes through an identical pipeline:

1. **Cleaning** — HTML tag stripping, entity decoding, boilerplate removal (footers, CTAs, cookie banners)
2. **Language Detection** — langdetect with graceful fallback to English for short texts
3. **Topic Tagging** — deterministic keyword frequency analysis across 9 health/science topic categories
4. **Chunking** — word-boundary-aware splitting with configurable size (500 words) and overlap (50 words)
5. **Trust Scoring** — weighted multi-factor scoring with abuse detection

This pipeline produces a normalized `ScrapedDocument` regardless of source type, ensuring consistent downstream behavior.

---

## 2. Topic Tagging Method

Topic tagging uses a **keyword frequency approach** rather than ML-based classification. This was a deliberate choice:

- **No external API dependencies** — works offline and in constrained deployment environments
- **Deterministic** — same input always produces same tags
- **Transparent** — the keyword lists are human-readable and auditable

The system maintains 9 topic categories (gut_health, nutrition, inflammation, mental_health, medicine, research, wellness, exercise, technology), each with 8-15 seed keywords. Scoring counts keyword hits per category and returns the top 5 by frequency.

**Limitation:** This approach favors explicit keyword usage. Content that discusses gut health conceptually without using specific terms may receive weaker tags. An embedding-based classifier would improve recall but adds model dependencies.

---

## 3. Trust Score Algorithm

### Design Philosophy

The trust score is designed to be **explainable, not just accurate**. Every score is accompanied by a `trust_breakdown` (per-factor scores), `risk_flags` (detected problems), and a `scoring_reason` (human-readable explanation). This transparency is the system's primary differentiator.

### Formula

```
trust_score = 0.30 × author_credibility
            + 0.20 × citation_count
            + 0.20 × domain_authority
            + 0.20 × recency
            + 0.10 × medical_disclaimer_presence
            - penalty(abuse_flags)
```

### Factor Scoring

| Factor | Approach |
|--------|----------|
| **Author Credibility** | Named credentials (MD, PhD) → 0.85; multiple authors → 0.9; institutional → 0.95; anonymous → 0.15 |
| **Citation Count** | Regex-detected references ([1], DOI links, "et al."); capped at 20 to prevent citation stuffing |
| **Domain Authority** | Tiered rubric: pubmed/nih.gov/edu → 1.0; Mayo Clinic/Harvard → 0.85; Healthline → 0.65; generic → 0.3 |
| **Recency** | <1 year → 0.95; 1-2 years → 0.8; 2-5 years → 0.55; >5 years → 0.25 with `outdated_medical_content` flag |
| **Medical Disclaimer** | Regex detection of "not medical advice" / "consult your doctor" patterns; small positive signal only |

### Abuse Prevention

The system actively detects manipulation through pattern matching:

- **SEO spam** — "buy now", "limited offer", "miracle cure" → `seo_spam_pattern` flag + 0.08 score penalty
- **Promotional language** — affiliate/discount patterns → `promotional_language` flag
- **Aggressive health claims** — "cures cancer", "guaranteed weight loss" → `aggressive_health_claims` flag
- **Missing attribution** — no author or date → respective flags with degraded factor scores

Each abuse flag incurs a 0.08 penalty from the raw weighted score, ensuring manipulative content is systematically downranked.

---

## 4. Edge Case Handling

| Scenario | Handling |
|----------|----------|
| Author not available | Score defaults to 0.15 (not zero); `missing_author` flag |
| Publish date missing | Recency defaults to 0.35; `missing_date` flag |
| Transcript unavailable | Returns 200 with description as fallback; `transcript_unavailable` flag |
| Multiple authors | Treated as strong signal (0.9); common in academic papers |
| Non-English content | Auto-detected via langdetect; `non_english` flag |
| Long articles | Word-based chunking with overlap prevents information loss |
| Citation stuffing | Citation contribution capped at 20 references |
| Scraper timeout | Returns structured 504 error with source_type context |

---

## 5. System Design: Ingestion + Evaluation

This system is intentionally designed as an **ingestion and evaluation pipeline**, not just a scraper. The scraping layer collects raw content; the pipeline layer transforms it into a normalized, scored, and explainable record.

The API layer has two operational modes:
- **Static dataset endpoints** (`/sources`, `/summary`) serve pre-generated data for fast, predictable review
- **Live scrape endpoint** (`POST /scrape`) demonstrates the pipeline works in real-time on arbitrary URLs

This split ensures reviewers see both reliable sample data and live functionality.

---

## 6. Limitations & Production Next Steps

**Current limitations:**
- No JavaScript rendering (SPA blogs may return incomplete content)
- Domain authority uses a static rubric, not live SEO metrics
- Single-threaded scraping (sequential, not parallel)
- No persistent storage for live scrape results
- No rate limiting on the API

**Production hardening would include:**
- Playwright/crawl4ai integration for JS-rendered pages
- Redis caching for repeat URL requests
- Background task queue (Celery) for async scraping
- API key authentication and rate limiting
- Scheduled re-scraping with change detection
- Database storage with deduplication
