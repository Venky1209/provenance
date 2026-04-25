# 🔍 Provenance — Content Trust Scoring API

> **Live Demo:** _[Deploy URL will go here after Railway deployment]_
>
> **API Docs:** _[Deploy URL]/docs_

Multi-source data scraping pipeline with **explainable trust scoring**. Scrapes blog posts, YouTube videos, and PubMed articles, then evaluates their reliability using a weighted, transparent scoring algorithm.

---

## Quick Start

```bash
# Clone
git clone https://github.com/Venky1209/provenance.git
cd provenance

# Setup
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

# Run the scraping pipeline (generates all output files)
python run_all.py

# Start the API server
uvicorn api.main:app --reload
```

Then open:
- **Dashboard:** http://localhost:8000/
- **API Docs:** http://localhost:8000/docs
- **Sample Data:** http://localhost:8000/sources

---

## Architecture

```
┌────────────────────────────────────────────────────┐
│                   run_all.py                       │
│          (Batch pipeline orchestrator)             │
└────────────┬───────────────────────────────────────┘
             │
   ┌─────────▼──────────┐
   │     scrapers/       │    Blog, YouTube, PubMed
   │  source-specific    │    HTTP + BS4, oEmbed,
   │  scraping logic     │    Entrez/Biopython
   └─────────┬───────────┘
             │ raw metadata + text
   ┌─────────▼──────────┐
   │     utils/          │    clean → detect_language
   │  cleaning &         │    → fingerprint
   │  normalization      │
   └─────────┬───────────┘
             │ cleaned text
   ┌─────────▼──────────┐
   │     pipeline/       │    chunk → tag_topics
   │  enrichment &       │    → compute_trust_score
   │  scoring            │
   └─────────┬───────────┘
             │ ScrapedDocument (normalized)
   ┌─────────▼──────────┐
   │     output/         │    sample_output.json
   │  scraped_data/      │    blogs.json, youtube.json,
   │  (artifacts)        │    pubmed.json, summary.json
   └─────────┬───────────┘
             │
   ┌─────────▼──────────┐
   │     api/            │    FastAPI endpoints
   │  GET /health        │    GET /sources
   │  GET /summary       │    GET /sources/{id}
   │  POST /scrape       │    GET / (dashboard)
   └─────────────────────┘
```

---

## Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/` | Dashboard UI — paste a URL, see trust score |
| `GET` | `/health` | Service status + build info |
| `GET` | `/summary` | Aggregate stats from sample dataset |
| `GET` | `/sources` | All 6 pre-scraped sample records |
| `GET` | `/sources/{id}` | Single record by stable source_id |
| `POST` | `/scrape` | **Live scrape** — accepts URL + source_type |
| `GET` | `/docs` | Interactive Swagger API documentation |

### POST /scrape — Request

```json
{
  "url": "https://www.healthline.com/nutrition/gut-microbiome-and-health",
  "source_type": "blog"
}
```

### POST /scrape — Response

```json
{
  "source_id": "a1b2c3d4e5f6",
  "source_url": "...",
  "source_type": "blog",
  "title": "How Does Your Gut Microbiome Affect Your Health?",
  "author": "Ruairi Robertson, PhD",
  "published_date": "2023-05-18",
  "language": "en",
  "topic_tags": ["gut_health", "nutrition", "research"],
  "trust_score": 0.47,
  "content_chunks": ["..."],
  "trust_breakdown": {
    "author_credibility": 0.60,
    "citation_count": 0.50,
    "domain_authority": 0.65,
    "recency": 0.80,
    "medical_disclaimer_presence": 0.20
  },
  "risk_flags": [],
  "scoring_reason": "Named author with credential. Mid-authority health publisher. Citations present. Recent content."
}
```

---

## Trust Score Design

### Formula

```
trust_score = f(author_credibility, citation_count, domain_authority, recency, medical_disclaimer_presence)
```

### Weights

| Factor | Weight | Logic |
|--------|--------|-------|
| `author_credibility` | **0.30** | Named clinician/researcher → high; anonymous → penalized |
| `citation_count` | **0.20** | Visible references, DOIs, PMIDs; capped at 20 to prevent stuffing |
| `domain_authority` | **0.20** | Tiered rubric: pubmed/gov/edu > health publisher > commercial > generic |
| `recency` | **0.20** | <1yr = 0.95, 1-2yr = 0.8, 2-5yr = 0.55, >5yr = 0.25 |
| `medical_disclaimer_presence` | **0.10** | Small positive signal only; never rescues bad content |

### Risk Flags (Abuse Prevention)

The system detects and downranks:

- `missing_author` — no identifiable author
- `missing_date` — publication date unavailable
- `no_citations` — zero references found
- `seo_spam_pattern` — "buy now", "miracle cure", etc.
- `promotional_language` — affiliate/discount patterns
- `aggressive_health_claims` — "cures cancer", "guaranteed weight loss"
- `outdated_medical_content` — content older than 5 years
- `non_english` — auto-detected non-English content
- `transcript_unavailable` — YouTube without transcript

### Edge Cases Handled

- **Missing metadata:** neutral-low fallback score (never zero)
- **Multiple authors:** treated as strong credibility signal
- **Non-English content:** auto-detected via langdetect, flagged
- **Long articles:** word-based chunking with configurable overlap
- **Transcript unavailable:** returns 200 with risk flag, not error

---

## Sources Scraped

| # | Source | Type | Trust Score |
|---|--------|------|-------------|
| 1 | Harvard Health — Gut feelings & mood | Blog | 0.53 |
| 2 | Healthline — Gut microbiome & health | Blog | 0.47 |
| 3 | MindBodyGreen — Signs of unhealthy gut | Blog | 0.34 |
| 4 | Kurzgesagt — How Bacteria Rule Your Body | YouTube | 0.35 |
| 5 | Erika Ebbel — Your Gut Microbiome | YouTube | 0.27 |
| 6 | PubMed — Gut Microbiome: Diet and Disease | PubMed | 0.74 |

---

## Output Files

```
output/
  sample_output.json     # All 6 records (full schema)
  summary.json           # Aggregate metrics

scraped_data/
  blogs.json             # 3 blog records (assignment format)
  youtube.json           # 2 YouTube records
  pubmed.json            # 1 PubMed record
```

---

## Project Structure

```
provenance/
├── api/                  # FastAPI application
│   ├── main.py           # App factory, CORS, dashboard route
│   ├── routes.py         # All endpoint handlers
│   └── dataset.py        # Sample data loader
├── scrapers/             # Source-specific scrapers
│   ├── base_scraper.py   # Abstract base + error handling
│   ├── blog_scraper.py   # BS4 metadata + content extraction
│   ├── youtube_scraper.py # oEmbed + transcript API
│   └── pubmed_scraper.py # Entrez E-utilities + HTML fallback
├── pipeline/             # Processing stages
│   ├── chunker.py        # Word-based overlapping chunks
│   ├── topic_tagger.py   # Keyword frequency tagging
│   └── trust_score.py    # Weighted scoring + abuse detection
├── utils/                # Shared helpers
│   ├── cleaner.py        # HTML stripping + noise removal
│   ├── language_detect.py # langdetect wrapper
│   └── fingerprint.py    # URL → stable source_id
├── templates/
│   └── index.html        # Dashboard UI
├── output/               # Generated artifacts
├── scraped_data/         # Per-type JSON (assignment format)
├── models.py             # Pydantic schemas
├── config.py             # URLs, paths, settings
├── run_all.py            # Batch pipeline entry point
├── requirements.txt      # Python dependencies
├── Procfile              # Railway/deployment
├── railway.json          # Railway config
└── REPORT.md             # Technical report
```

---

## Tools & Libraries

| Library | Purpose |
|---------|---------|
| **FastAPI** | REST API framework |
| **BeautifulSoup4** + **lxml** | HTML parsing and content extraction |
| **youtube-transcript-api** | YouTube transcript retrieval |
| **Biopython** (Entrez) | PubMed article metadata via NCBI API |
| **langdetect** | Automatic language detection |
| **Pydantic v2** | Data validation and serialization |
| **uvicorn** | ASGI server |
| **requests** | HTTP client |

---

## Limitations

- **No JavaScript rendering** — SPA-heavy blogs may return incomplete content
- **YouTube transcript dependency** — videos without captions get degraded results
- **Domain authority is rule-based** — uses a tiered rubric, not live SEO APIs
- **No persistent storage** — live scrape results are ephemeral
- **Rate limiting** — no built-in rate limiting; PubMed has NCBI usage policies
- **Single-threaded scraping** — sources are scraped sequentially

---

## Deployment (Railway)

1. Connect repo to Railway
2. Railway auto-detects Python + `requirements.txt`
3. Start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
4. Health check: `/health`
5. No database or environment variables required