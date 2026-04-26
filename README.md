<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0a0a0f,30:0d1117,60:161b22,100:1a1f2e&height=220&section=header&text=PROVENANCE&fontSize=80&fontColor=e6edf3&fontAlignY=40&desc=Multi-Source%20Content%20Ingestion%20%26%20Trust%20Scoring%20Pipeline&descAlignY=62&descSize=16&descColor=8b949e&animation=fadeIn&fontAlign=50" width="100%"/>

<!-- TYPING ANIMATION -->
<a href="https://git.io/typing-svg">
  <img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=500&size=16&pause=1000&color=58A6FF&center=true&vCenter=true&width=600&lines=Scrape+%E2%86%92+Clean+%E2%86%92+Enrich+%E2%86%92+Score+%E2%86%92+Serve;Explainable+trust+scoring+grounded+in+E-E-A-T;Built+as+a+real-world+RAG+data+ingestion+layer;FastAPI+%7C+Railway+%7C+Python+3.13" alt="Typing SVG" />
</a>

<br/><br/>

<!-- LIVE BUTTONS -->
<a href="https://web-production-e20d3.up.railway.app/">
  <img src="https://img.shields.io/badge/?%20LIVE%20DEMO-00D4AA?style=for-the-badge&logo=railway&logoColor=white&labelColor=0d1117"/>
</a>
&nbsp;
<a href="https://web-production-e20d3.up.railway.app/docs">
  <img src="https://img.shields.io/badge/?%20API%20DOCS-85EA2D?style=for-the-badge&logo=swagger&logoColor=white&labelColor=0d1117"/>
</a>
&nbsp;
<a href="https://github.com/Venky1209/provenance/stargazers">
  <img src="https://img.shields.io/github/stars/Venky1209/provenance?style=for-the-badge&logo=github&labelColor=0d1117&color=f0e68c"/>
</a>

<br/><br/>

<!-- DYNAMIC SKILL ICONS -->
<img src="https://skillicons.dev/icons?i=python,fastapi,github,vscode&theme=dark" />

<br/><br/>

<!-- STAT PILLS -->
<img src="https://img.shields.io/badge/sources-6%20scraped-1f6feb?style=flat-square"/>
<img src="https://img.shields.io/badge/pipeline-scrape%20%E2%86%92%20clean%20%E2%86%92%20chunk%20%E2%86%92%20score-3fb950?style=flat-square"/>
<img src="https://img.shields.io/badge/scoring-deterministic%20%7C%20auditable-d29922?style=flat-square"/>
<img src="https://img.shields.io/badge/deploy-railway-8957e5?style=flat-square"/>

</div>

<br/>

---

<div align="center">

`
 Provenance is a modular data ingestion and trust evaluation pipeline.
 Scrapes blogs, YouTube, and PubMed — scores each source with a
 transparent, explainable formula. Built as a compact RAG data layer.
`

</div>

---

## ? Quick Start

`ash
# Clone & install
git clone https://github.com/Venky1209/provenance.git
cd provenance

python -m venv venv
source venv/bin/activate          # macOS/Linux
# venv\Scripts\activate           # Windows

pip install -r requirements.txt

# Run full pipeline — generates all output JSON
python run_all.py

# Start API server
uvicorn api.main:app --reload
`

> **Dashboard** ? http://localhost:8000/  
> **API Docs** ? http://localhost:8000/docs  
> **Live Demo** ? [web-production-e20d3.up.railway.app](https://web-production-e20d3.up.railway.app/)

---

## ? Architecture

`
+-----------------------------------------------------------------+
¦  run_all.py  ·  Batch pipeline orchestrator                      ¦
+-----------------------------------------------------------------+
                           ¦
          +----------------?-----------------+
          ¦  scraper/                         ¦
          ¦  +-- base_scraper.py              ¦  Abstract base + retry logic
          ¦  +-- blog_scraper.py              ¦  requests + BS4 + lxml
          ¦  +-- youtube_scraper.py           ¦  oEmbed + transcript-api
          ¦  +-- pubmed_scraper.py            ¦  Biopython Entrez XML
          +----------------------------------+
                           ¦  raw text + metadata
          +----------------?-----------------+
          ¦  utils/                           ¦
          ¦  +-- cleaner.py                   ¦  strip HTML · normalize whitespace
          ¦  +-- language_detect.py           ¦  langdetect ? ISO 639-1
          ¦  +-- chunking.py                  ¦  500-word chunks · 50-word overlap
          ¦  +-- tagging.py                   ¦  keyword-frequency topic tags
          ¦  +-- fingerprint.py               ¦  SHA-256 dedup hash
          +----------------------------------+
                           ¦  enriched document
          +----------------?-----------------+
          ¦  scoring/                         ¦
          ¦  +-- trust_score.py               ¦  weighted score + tiered penalties
          +----------------------------------+
                           ¦  ScrapedDocument · Pydantic v2
          +----------------?-----------------+
          ¦  output/  +  scraped_data/        ¦  JSON artifacts on disk
          +----------------------------------+
                           ¦
          +----------------?-----------------+
          ¦  api/  ·  FastAPI                 ¦
          ¦  GET /   POST /scrape   /docs     ¦
          +----------------------------------+
`

---

## ? API Reference

| Method | Route | Description |
|--------|-------|-------------|
| \GET\ | \/\ | Dashboard — paste any URL, see live scored result |
| \GET\ | \/health\ | Service status + version info |
| \GET\ | \/sources\ | All 6 pre-scraped sample records |
| \GET\ | \/sources/{id}\ | Single record with full trust breakdown |
| \GET\ | \/summary\ | Aggregate stats + ranked trust scores |
| \POST\ | \/scrape\ | Live scrape + score any URL in real time |
| \GET\ | \/docs\ | Interactive Swagger UI |

<details>
<summary><b>POST /scrape — Request & Response</b></summary>

**Request**
`json
{
  "url": "https://lilianweng.github.io/posts/2023-06-23-agent/",
  "source_type": "blog"
}
`

**Response**
`json
{
  "source_id": "8b3f9d1a2c4e",
  "source_url": "https://lilianweng.github.io/posts/2023-06-23-agent/",
  "source_type": "blog",
  "title": "LLM Powered Autonomous Agents",
  "author": "Lilian Weng",
  "published_date": "2023-06-23",
  "language": "en",
  "region": "us",
  "topic_tags": ["artificial_intelligence", "technology", "research"],
  "trust_score": 0.57,
  "content_chunks": ["..."],
  "trust_breakdown": {
    "author_credibility": 0.60,
    "citation_count": 0.35,
    "domain_authority": 0.65,
    "recency": 0.80,
    "medical_disclaimer_presence": 0.20
  },
  "risk_flags": [],
  "scoring_reason": "Named individual without explicit credentials. Found 35 visible citations. Recognized authority tier. Published within 2 years. No disclaimer found."
}
`

</details>

---

## ? Trust Score Design

The scoring formula is fully deterministic and auditable — no ML, no black box.

`
trust_score = S(factor_score × weight) - S(tiered penalty per flag)

floor ? 0.05   (absence of signal ? confirmed untrustworthy)
ceil  ? 1.00
`

### Weights

| Factor | Weight | Scoring Logic |
|--------|--------|---------------|
| \uthor_credibility\ | **0.30** | MD / PhD / Institution ? 1.0 · Named individual ? 0.6 · Anonymous ? 0.1 |
| \citation_count\ | **0.20** | DOI / PMID / \[n]\ pattern detection · log-scaled · capped at 20 |
| \domain_authority\ | **0.20** | Tiered rubric: \pubmed/gov/edu\ ? health publisher ? commercial ? generic |
| \ecency\ | **0.20** | \<1yr=0.95\ · \1-2yr=0.80\ · \2-5yr=0.55\ · \>5yr=0.25\ · \missing=0.30\ |
| \medical_disclaimer\ | **0.10** | Weak positive signal only — never rescues low-quality content |

### Risk Flags & Abuse Prevention

Grounded in [DISCERN](https://pmc.ncbi.nlm.nih.gov/articles/PMC1756830/), [Google E-E-A-T](https://developers.google.com/search/docs/fundamentals/creating-helpful-content), and [HONcode](https://pmc.ncbi.nlm.nih.gov/articles/PMC6158347/) credibility principles.

| Flag | Trigger | Penalty |
|------|---------|---------|
| \missing_author\ | No identifiable author found | -0.10 |
| \missing_date\ | Publication date absent | -0.07 |
| \suspicious_author\ | "admin" / "staff" / single initial | -0.15 |
| \seo_spam_pattern\ | "miracle cure", "buy now", etc. | -0.20 |
| \promotional_language\ | Affiliate links, discount codes | -0.12 |
| \ggressive_health_claims\ | "cures cancer", "guaranteed results" | -0.25 |
| \outdated_medical_content\ | Medical content older than 5 years | -0.10 |
| \
on_english\ | Auto-detected non-English language | -0.05 |
| \	ranscript_unavailable\ | YouTube video without captions | -0.05 |

### Edge Cases Handled

| Scenario | Handling |
|----------|----------|
| Missing author | Neutral-low fallback · \missing_author\ flag applied |
| Missing date | \ecency=0.30\ fallback · \missing_date\ flag applied |
| Multiple authors | Treated as strong credibility signal ? boosted score |
| Non-English content | Auto-detected via langdetect · soft penalty applied |
| Transcript unavailable | Returns \200\ with flag · does not error |
| Long articles | Word-based chunking with configurable overlap |

---

## ? Sample Dataset

Sources chosen across a trust spectrum — proving the system is discriminative, not decorative.

| # | Source | Type | Score | Key Signal |
|---|--------|------|-------|------------|
| 1 | Lilian Weng — LLM Autonomous Agents | Blog | **0.57** | Named researcher · 35 citations |
| 2 | BAIR — Koala Dialogue Model | Blog | **0.49** | Institutional blog · moderate citations |
| 3 | HuggingFace — Foundation model labeling | Blog | **0.38** | No explicit author · fewer references |
| 4 | PubMed — Molecular characterization | PubMed | **0.57** | Peer-reviewed · multi-author |
| 5 | MKBHD — Auto Focus | YouTube | **0.35** | No transcript · no citations |
| 6 | 3Blue1Brown — Neural Networks | YouTube | **0.28** | Auto-generated captions only |

---

## ? Output Files

`
output/
  scraped_data.json          # All 6 records — full schema
  summary.json               # Aggregate metrics + ranked scores

scraped_data/
  blogs.json                 # 3 blog records  (assignment schema)
  youtube.json               # 2 YouTube records
  pubmed.json                # 1 PubMed record
`

---

## ? Project Structure

`
provenance/
+-- api/
¦   +-- main.py               # App factory · CORS · static routes
¦   +-- routes.py             # All endpoint handlers
¦   +-- dataset.py            # JSON artifact loader
¦
+-- scraper/
¦   +-- base_scraper.py       # Abstract base · retry · error handling
¦   +-- blog_scraper.py       # OpenGraph/meta + semantic content extraction
¦   +-- youtube_scraper.py    # oEmbed metadata + transcript API
¦   +-- pubmed_scraper.py     # Biopython Entrez esearch/efetch
¦
+-- scoring/
¦   +-- trust_score.py        # Weighted scoring + tiered penalty engine
¦
+-- utils/
¦   +-- tagging.py            # Keyword-frequency topic tagger
¦   +-- chunking.py           # Overlapping word-based chunker
¦   +-- cleaner.py            # HTML strip + whitespace normalize
¦   +-- language_detect.py    # langdetect ? ISO 639-1
¦   +-- fingerprint.py        # SHA-256 content hash for deduplication
¦
+-- templates/
¦   +-- index.html            # Dark-mode dashboard (vanilla JS)
¦
+-- models.py                 # Pydantic v2 schemas
+-- config.py                 # URLs · chunk size · scoring weights
+-- run_all.py                # Single-command pipeline runner
+-- requirements.txt
+-- Procfile                  # Railway start command
+-- railway.json              # Railway deploy config
¦
+-- REPORT.md                 # Technical report (assignment)
+-- DECISIONS.md              # Architecture decision log
+-- WHAT_I_WOULD_BUILD_NEXT.md
`

---

## ? Tech Stack

<div align="center">

<img src="https://skillicons.dev/icons?i=python,fastapi,github,git&theme=dark&perline=4"/>

</div>

<br/>

| Library | Purpose |
|---------|---------|
| \astapi\ | REST API framework |
| \uvicorn\ | ASGI server |
| \eautifulsoup4\ + \lxml\ | HTML parsing + content extraction |
| \youtube-transcript-api\ | YouTube caption retrieval |
| \iopython\ | PubMed NCBI Entrez XML API |
| \langdetect\ | Language detection ? ISO 639-1 |
| \pydantic v2\ | Data validation + serialization |
| \equests\ | HTTP client |

---

## ? Limitations

| Limitation | Production Fix |
|------------|----------------|
| No JS rendering — SPAs return incomplete content | Playwright / Crawl4AI fallback |
| YouTube without transcripts gets degraded score | Whisper ASR on audio stream |
| Domain authority is a static rubric, not live data | Moz / Majestic API integration |
| Live scrape results are ephemeral | PostgreSQL append-only log |
| Sequential scraping — slow on large batches | \syncio\ concurrent pipeline |
| No robots.txt compliance checking | Respectful crawl layer in BaseScraper |

---

## ? Deployment

Deployed on **Railway** — zero-config serverless Python.

`
web: uvicorn api.main:app --host 0.0.0.0 --port $PORT
`

No environment variables required. No database. Cold start under 5s.  
Connect repo ? Railway auto-detects Python + \equirements.txt\ ? done.

---

## ? Documentation

| File | Contents |
|------|----------|
| [\REPORT.md\](./REPORT.md) | Scraping strategy · scoring algorithm · edge case handling |
| [\DECISIONS.md\](./DECISIONS.md) | Why BS4 over Crawl4AI · why explainable over ML scoring |
| [\WHAT_I_WOULD_BUILD_NEXT.md\](./WHAT_I_WOULD_BUILD_NEXT.md) | Phase 2 — discovery engine · async pipeline · vector embeddings |

---

<div align="center">

<!-- GITHUB STATS -->
<img src="https://github-readme-stats.vercel.app/api/pin/?username=Venky1209&repo=provenance&theme=github_dark&hide_border=true&bg_color=0d1117&title_color=58a6ff&text_color=8b949e&icon_color=58a6ff" />

<br/><br/>

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:1a1f2e,50:161b22,100:0d1117&height=100&section=footer&animation=fadeIn" width="100%"/>

<sub>Built by <a href="https://github.com/Venky1209">Venky1209</a> &nbsp;·&nbsp; FastAPI &nbsp;·&nbsp; Railway &nbsp;·&nbsp; Python 3.13</sub>

</div>
