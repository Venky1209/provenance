# Technical Report: Provenance

## 1. Scraping Strategy
The system implements a source-specific scraper pattern inheriting from a `BaseScraper`, prioritizing deployment speed and resilience.

- **Blogs**: Uses `requests` and `BeautifulSoup4` with heuristic extraction chains (e.g., `<article>` → `<main>` → `#content`). Metadata is extracted via OpenGraph tags.
- **YouTube**: Uses the oEmbed API for video metadata and `youtube-transcript-api` for raw captions, avoiding brittle DOM scraping of the YouTube player.
- **PubMed**: Avoids HTML parsing entirely by using Biopython's Entrez E-utilities to fetch structured XML directly from the NCBI database. 

## 2. Topic Tagging Method
Topic tagging uses **deterministic keyword frequency analysis** rather than ML classification. This ensures the system runs without external API dependencies and provides perfectly auditable results. 

The taxonomy includes health, science, technology, business, and society categories. Text chunks are tokenized, normalized, and scored against topic dictionaries. The system returns up to 5 topics sorted by hit density. While this favors explicit keyword usage over semantic nuance, it guarantees predictable explainability.

## 3. Trust Score Algorithm
The 0.0-1.0 trust score is explainable, deterministic, and grounded in E-E-A-T principles. It avoids black-box weighting.

**Base Formula (Weighted Sum):**
- **Author Credibility (30%)**: Institutional (0.95), MD/PhD (0.85), Multiple (0.9), Anonymous (0.15).
- **Citation Count (20%)**: Regex detection of DOIs, PMIDs, or standard academic references, capped at 20.
- **Domain Authority (20%)**: Tiered rubric (.gov/pubmed = 1.0, Mayo Clinic = 0.85, Healthline = 0.65).
- **Recency (20%)**: Time decay (<1yr = 0.95, 2-5yrs = 0.55).
- **Medical Disclaimer (10%)**: Positive signal for "not medical advice" patterns.

**Abuse Prevention Logic:**
The pipeline actively detects manipulation and applies strict scoring rules to prevent abuse:
- **Fake Authors**: The system cross-checks author names against known organizational markers and credential keywords (MD, PhD). Generic handles or suspicious names (e.g. "admin") incur a `suspicious_author` penalty and low credibility scores.
- **SEO Spam Blogs**: Domains with low or unknown authority are heavily penalized. The system uses a tiered rubric, granting high authority to `.gov`, `.edu`, and known medical repositories, while assigning minimal weight to standard blogs or unrecognized domains. It also scans for SEO spam patterns (e.g., "buy now", "miracle cure") and applies a `-0.20` hard penalty.
- **Misleading Medical Content**: The text is scanned for standard medical disclaimers ("not medical advice", "for informational purposes"). A lack of a disclaimer penalizes the score, reducing the overall trust rating for the content.
- **Outdated Information**: Medical and scientific information decays rapidly. A strong recency penalty is applied based on a time-decay formula: content older than 5 years receives a significant penalty, while immediate/recent publications retain high scores.

## 4. Edge Case Handling

The system was designed to robustly handle the following scenarios:

| Edge Case | System Handling |
|-----------|-----------------|
| **Missing Metadata (Author)** | Score defaults to a baseline low weight (0.15); emits `missing_author` flag. |
| **Missing Metadata (Date)** | Recency defaults to a low baseline (0.35); emits `missing_date` flag. |
| **Missing Metadata (Transcript)** | Degrades gracefully by falling back to scraping the video description; emits `transcript_unavailable` flag. |
| **Multiple Authors** | Detects multiple names (journal-style) and applies an average/high credibility score (0.75). |
| **Non-English Content** | Auto-detected via `langdetect`; emits `non_english` penalty flag and normalizes the language field. |
| **Long Articles** | Ensured via `chunking.py`: word-based chunking (500 words with 50-word overlap) splits long texts so processing and tagging work reliably. |
| **Citation Stuffing** | Citation contribution to the score is strictly capped at a maximum of 20 references to prevent gaming the metric. |
